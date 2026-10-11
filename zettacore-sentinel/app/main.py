from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from app.intel import lookup_urlhaus

APP_VERSION = "0.3.0"
CONTROL = re.compile(r"[\x00-\x20\x7f]")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
HOST_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
HEX_ESCAPE = re.compile(r"%[0-9a-fA-F]{2}")
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "cutt.ly", "rb.gy", "shorturl.at", "lnkd.in", "rebrand.ly", "short.io", "linktr.ee"}
SUSPICIOUS_TERMS = {"account", "billing", "confirm", "gift", "login", "password", "payment", "recover", "security", "signin", "suspended", "update", "verify", "verification", "wallet", "prize"}
BRAND_DOMAINS = {
    "amazon": ("amazon.com", "amazon.co.uk", "amazon.es", "amazon.de", "amazon.fr"),
    "apple": ("apple.com", "icloud.com"),
    "bbva": ("bbva.es", "bbva.com"),
    "facebook": ("facebook.com", "fb.com"),
    "google": ("google.com", "google.co.uk", "google.es", "gmail.com"),
    "instagram": ("instagram.com",),
    "microsoft": ("microsoft.com", "microsoftonline.com", "office.com", "live.com"),
    "netflix": ("netflix.com",),
    "paypal": ("paypal.com",),
    "santander": ("santander.com", "santander.es"),
    "whatsapp": ("whatsapp.com",),
}
CONFUSABLE_TRANSLATION = str.maketrans({"0": "o", "3": "e", "5": "s", "7": "t", "8": "b"})

app = FastAPI(
    title="ZettaCore Sentinel API",
    version=APP_VERSION,
    description="Privacy-minded URL triage with local heuristics and optional consent-gated URLhaus lookup.",
    docs_url="/api/docs",
    redoc_url=None,
)


class RequestHardeningMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            content_length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return JSONResponse({"detail": "Cabecera Content-Length no válida."}, status_code=400)
        if content_length > 12288:
            return JSONResponse({"detail": "La petición supera el tamaño máximo permitido."}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(RequestHardeningMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


class AnalyzeRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)
    external_lookup_consent: bool = False

    @field_validator("url")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Introduce una URL.")
        if CONTROL.search(value):
            raise ValueError("La URL contiene espacios internos o caracteres de control.")
        if "\\" in value:
            raise ValueError("La URL contiene barras inversas ambiguas; revisa el enlace original.")
        return value


def _parse_url(raw: str):
    value = raw.strip()
    if not value or CONTROL.search(value):
        raise ValueError("Introduce una URL válida sin espacios internos ni caracteres de control.")
    if "\\" in value:
        raise ValueError("La URL contiene barras inversas ambiguas; revisa el enlace original.")
    if "://" not in value and SCHEME.match(value):
        prefix, remainder = value.split(":", 1)
        looks_like_host_port = bool(re.fullmatch(r"(?:\[[0-9a-fA-F:]+\]|[^/:\s]+)", prefix)) and remainder[:1].isdigit()
        if not looks_like_host_port:
            raise ValueError("Solo se admiten enlaces HTTP o HTTPS.")
    candidate = value if "://" in value else "https://" + value
    try:
        parsed = urlsplit(candidate)
        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"}:
            raise ValueError("Solo se admiten enlaces HTTP o HTTPS.")
        if not parsed.hostname:
            raise ValueError("No se ha podido identificar el dominio.")
        if "%" in parsed.hostname:
            raise ValueError("El dominio contiene una codificación ambigua.")
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("El puerto de la URL no es válido.") from exc
        raw_host = parsed.hostname.rstrip(".")
        try:
            ip_obj = ipaddress.ip_address(raw_host.strip("[]"))
            host, ip_version = ip_obj.compressed.lower(), ip_obj.version
        except ValueError:
            ip_obj, ip_version = None, None
            try:
                host = raw_host.encode("idna").decode("ascii").lower()
            except UnicodeError as exc:
                raise ValueError("El dominio no tiene un formato válido.") from exc
            if not host or len(host) > 253:
                raise ValueError("La longitud del dominio no es válida.")
            if any(not HOST_LABEL.fullmatch(label) for label in host.split(".")):
                raise ValueError("El dominio contiene una etiqueta no válida.")
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("El puerto debe estar entre 1 y 65535.")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("No se ha podido interpretar esta URL.") from exc
    return value, parsed, scheme, host, port, ip_obj, ip_version


def normalize_url(raw: str) -> str:
    """Return only the origin; never echo credentials, path, query, or fragment."""
    _, _, scheme, host, port, _, ip_version = _parse_url(raw)
    authority_host = "[" + host + "]" if ip_version == 6 else host
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    authority = authority_host if port is None or default_port else f"{authority_host}:{port}"
    return urlunsplit((scheme, authority, "/", "", ""))


def _external_query_url(raw: str) -> str:
    """Canonical URL for an explicitly consented provider lookup; strips userinfo and fragments."""
    _, parsed, scheme, host, port, _, ip_version = _parse_url(raw)
    authority_host = "[" + host + "]" if ip_version == 6 else host
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    authority = authority_host if port is None or default_port else f"{authority_host}:{port}"
    return urlunsplit((scheme, authority, parsed.path or "/", parsed.query, ""))


def _distance_one_or_less(left: str, right: str) -> bool:
    if left == right:
        return True
    if abs(len(left) - len(right)) > 1:
        return False
    i = j = edits = 0
    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            i += 1
            j += 1
        else:
            edits += 1
            if edits > 1:
                return False
            if len(left) > len(right):
                i += 1
            elif len(right) > len(left):
                j += 1
            else:
                i += 1
                j += 1
    if i < len(left) or j < len(right):
        edits += 1
    return edits <= 1


def _is_domain_or_subdomain(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)


def analyze(raw: str) -> dict:
    value, parsed, scheme, host, port, ip_obj, ip_version = _parse_url(raw)
    score, findings, seen_ids = 0, [], set()

    def add(identifier: str, points: int, severity: str, title: str, detail: str, evidence: str = ""):
        nonlocal score
        if identifier in seen_ids:
            return
        seen_ids.add(identifier)
        score += points
        findings.append({"id": identifier, "severity": severity, "points": points, "title": title, "detail": detail, "evidence": evidence})

    if scheme != "https":
        add("http", 15, "medium", "La URL no usa HTTPS", "La conexión no está protegida por TLS en esta URL.", "Esquema: HTTP")
    if parsed.username is not None or parsed.password is not None:
        add("userinfo", 30, "high", "Hay información antes del dominio", "El texto antes de @ puede hacer que un enlace parezca pertenecer a otra web. Comprueba el host real.", "La autoridad contiene credenciales o userinfo")
    if ip_obj is not None:
        if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_unspecified or ip_obj.is_multicast:
            add("nonpublic_ip", 35, "high", "La IP no es una dirección pública normal", "La IP pertenece a un rango local, privado, reservado o especial. Sentinel no ha intentado conectarse a ella.", f"IPv{ip_version}: {host}")
        else:
            add("ip_host", 18, "medium", "El host es una dirección IP", "Usar una IP no implica fraude, pero dificulta confirmar la identidad del servicio.", f"IPv{ip_version}: {host}")
    elif re.fullmatch(r"[0-9.]+", host):
        add("numeric_host", 25, "high", "El host usa un formato numérico ambiguo", "Algunos clientes interpretan direcciones numéricas no canónicas de forma distinta.", f"Host: {host}")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".test")):
        add("local_name", 30, "high", "El dominio parece local o interno", "El nombre suele reservarse para pruebas o redes privadas, no para un servicio público habitual.", f"Host: {host}")
    if any(label.startswith("xn--") for label in host.split(".")):
        add("idn_punycode", 15, "medium", "El dominio contiene una etiqueta IDN en punycode", "Los dominios internacionalizados pueden ser legítimos, pero a veces imitan visualmente otros dominios. Comprueba el nombre por otro canal.", f"Host normalizado: {host}")
    if any(_is_domain_or_subdomain(host, shortener) for shortener in SHORTENERS):
        add("shortener", 12, "medium", "El enlace usa un acortador conocido", "El destino final no se puede deducir solo mirando el enlace corto. Confirma quién lo envió.", f"Host: {host}")

    labels = host.split(".")
    for brand, official_domains in BRAND_DOMAINS.items():
        if any(_is_domain_or_subdomain(host, domain) for domain in official_domains):
            continue
        normalized_labels = set()
        for label in labels:
            candidates = {label, label.translate(CONFUSABLE_TRANSLATION), label.replace("1", "i"), label.replace("1", "l")}
            for token in label.split("-"):
                candidates.add(token)
                candidates.add(token.translate(CONFUSABLE_TRANSLATION))
                candidates.add(token.replace("1", "i"))
                candidates.add(token.replace("1", "l"))
            normalized_labels.update(candidates)
        if any(brand in label.replace("-", "") for label in labels):
            add(f"brand_impersonation_{brand}", 25, "high", "El dominio menciona una marca fuera de dominios conocidos", f"El host incluye “{brand}”, pero no termina en uno de los dominios de referencia configurados. Es una señal de comprobación, no prueba definitiva de fraude.", f"Marca: {brand}; host: {host}")
        elif any(_distance_one_or_less(candidate, brand) for candidate in normalized_labels if len(candidate) >= 5 and len(brand) >= 5):
            add(f"brand_typo_{brand}", 22, "high", "Posible variante tipográfica de una marca", f"Una etiqueta del dominio es visual o tipográficamente parecida a “{brand}”. Comprueba el dominio oficial de forma independiente.", f"Marca comparada: {brand}; host: {host}")

    if len(labels) >= 5:
        add("deep_subdomains", 8, "low", "El dominio tiene muchas subetiquetas", "Varios niveles pueden hacer que la parte importante del dominio pase desapercibida.", f"Número de etiquetas: {len(labels)}")
    if host.count("-") >= 3:
        add("many_hyphens", 6, "low", "El host contiene varios guiones", "Los guiones son normales en muchos dominios, pero una cantidad inusual dificulta leer el nombre.", f"Guiones: {host.count('-')}")
    if port is not None and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
        add("nonstandard_port", 8, "low", "La URL usa un puerto no habitual", "Puede ser legítimo, pero conviene comprobar por qué el servicio usa otro puerto.", f"Puerto: {port}")

    path_and_query = (parsed.path + "?" + parsed.query).lower()
    terms = sorted(term for term in SUSPICIOUS_TERMS if re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", path_and_query))
    if terms:
        add("social_engineering_terms", min(12, 3 + 2 * len(terms)), "low", "La ruta incluye términos habituales en señuelos", "Estas palabras también aparecen en páginas legítimas; por sí solas no determinan el riesgo.", "Términos: " + ", ".join(terms))
    if HEX_ESCAPE.search(parsed.path + "?" + parsed.query):
        add("encoded_url", 4, "low", "La ruta contiene caracteres codificados", "La codificación URL es normal, aunque puede dificultar leer una parte de la ruta.", "Se encontraron secuencias %XX")

    score = min(score, 100)
    if score >= 55:
        risk, label, advice = "high", "Varias señales de riesgo", "No introduzcas credenciales ni datos de pago. Abre la web oficial escribiendo su dirección tú mismo y verifica el mensaje por otro canal."
    elif score >= 25:
        risk, label, advice = "medium", "Requiere comprobación", "No sigas el enlace desde el mensaje. Comprueba el dominio completo y confirma el remitente por un canal independiente."
    elif score > 0:
        risk, label, advice = "low", "Algunas señales para revisar", "La señal detectada no demuestra fraude. Revisa el dominio y el contexto antes de continuar."
    else:
        risk, label, advice = "unverified", "Sin señales destacadas · no verificado", "No se han detectado las señales heurísticas incluidas en esta versión. Eso no confirma que el enlace sea auténtico ni seguro."

    origin = normalize_url(value)
    return {
        "product": "ZettaCore Sentinel",
        "version": APP_VERSION,
        "analysis_mode": "local_heuristics_only",
        "risk": risk,
        "risk_label": label,
        "indicator_score": score,
        "score_interpretation": "Puntuación heurística interna; no es probabilidad de fraude.",
        "hostname": host,
        "origin": origin,
        "findings": findings,
        "findings_count": len(findings),
        "advice": advice,
        "external_reputation_checked": False,
        "external_intelligence": {"provider": "URLhaus", "status": "not_requested", "checked": False, "summary": "No se ha solicitado una consulta externa."},
        "target_fetched": False,
        "limitations": [
            "No se ha visitado el enlace ni seguido redirecciones.",
            "No se han consultado listas de bloqueo ni reputación externa.",
            "La puntuación no es una probabilidad y puede producir falsos positivos o negativos.",
            "Una URL sin señales detectadas no queda certificada como segura.",
            "La lista de marcas y dominios conocidos es limitada y puede quedar desactualizada.",
        ],
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "product": "ZettaCore Sentinel", "version": APP_VERSION}


@app.post("/api/analyze")
async def analyze_url(payload: AnalyzeRequest):
    try:
        result = analyze(payload.url)
        if not payload.external_lookup_consent:
            return result

        if any(item["id"] == "userinfo" for item in result["findings"]):
            intel = {
                "provider": "URLhaus",
                "status": "skipped_sensitive_url",
                "checked": False,
                "summary": "La URL contiene información antes del dominio; no se ha compartido con la fuente externa.",
            }
        else:
            intel = await lookup_urlhaus(_external_query_url(payload.url))

        result["external_intelligence"] = intel
        result["external_reputation_checked"] = bool(intel.get("checked"))
        if result["external_reputation_checked"]:
            result["limitations"] = [
                item for item in result["limitations"]
                if item != "No se han consultado listas de bloqueo ni reputación externa."
            ]
            result["limitations"].append(
                "La fuente URLhaus cubre indicadores relacionados con malware; no detecta todas las formas de phishing."
            )
        if intel.get("status") == "listed":
            result["findings"].append({
                "id": "external_urlhaus_match",
                "severity": "high",
                "points": 45,
                "title": "Coincidencia en URLhaus",
                "detail": "La fuente externa relaciona esta URL con distribución de malware. El registro puede estar inactivo o desactualizado; no prueba que el destino esté activo ahora.",
                "evidence": "URLhaus; estado del registro: " + str(intel.get("url_status", "desconocido")),
            })
            result["findings_count"] = len(result["findings"])
            result["indicator_score"] = min(100, max(result["indicator_score"] + 45, 80))
            result["risk"] = "high"
            result["risk_label"] = "Coincidencia en inteligencia externa"
            result["advice"] = "No descargues archivos ni introduzcas datos en este enlace. URLhaus tiene una entrada asociada a distribución de malware; confirma cualquier alerta mediante canales de confianza."
            result["analysis_mode"] = "heuristics_plus_external_lookup"
        elif intel.get("status") == "no_match":
            result["analysis_mode"] = "heuristics_plus_external_lookup"
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/", response_class=HTMLResponse)
def home():
    with open("app/static/index.html", encoding="utf-8") as file:
        return file.read()
