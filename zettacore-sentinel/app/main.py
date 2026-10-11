from __future__ import annotations
import ipaddress, re
from urllib.parse import urlsplit, urlunsplit
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="ZettaCore Sentinel API", version="0.1.0",
              description="Heuristic URL risk indicators; not a safety guarantee.")
SHORTENERS={"bit.ly","tinyurl.com","t.co","goo.gl","ow.ly","is.gd","buff.ly","cutt.ly","rb.gy","shorturl.at"}
WORDS={"login","verify","verification","password","wallet","secure","update","account","signin","confirm","billing","gift","prize"}
BRANDS={"paypal","microsoft","apple","google","amazon","facebook","instagram","whatsapp","netflix","santander","bbva"}
CONTROL=re.compile(r"[\x00-\x20\x7f]")
HEX=re.compile(r"%[0-9a-fA-F]{2}")

class AnalyzeRequest(BaseModel):
    url: str = Field(min_length=4,max_length=2048)
    @field_validator("url")
    @classmethod
    def valid_text(cls,v):
        v=v.strip()
        if CONTROL.search(v): raise ValueError("La URL contiene caracteres no permitidos.")
        return v

def normalize_url(raw:str)->str:
    candidate=raw.strip()
    if not candidate: raise ValueError("Introduce una URL.")
    if "://" not in candidate: candidate="https://"+candidate
    p=urlsplit(candidate)
    if p.scheme.lower() not in {"http","https"}: raise ValueError("Solo se admiten URLs HTTP o HTTPS.")
    if not p.hostname: raise ValueError("No se ha podido identificar el dominio.")
    try: host=p.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    except UnicodeError as e: raise ValueError("El dominio no tiene un formato válido.") from e
    try: port=p.port
    except ValueError as e: raise ValueError("El puerto no es válido.") from e
    netloc=host+(f":{port}" if port is not None else "")
    return urlunsplit((p.scheme.lower(),netloc,p.path or "/",p.query,""))

def analyze(raw:str)->dict:
    normalized=normalize_url(raw)
    source=urlsplit(raw if "://" in raw else "https://"+raw)
    p=urlsplit(normalized); host=p.hostname or ""; score=0; findings=[]
    def add(points,level,title,detail):
        nonlocal score
        score+=points; findings.append({"level":level,"title":title,"detail":detail})
    if p.scheme!="https": add(15,"medium","La conexión no usa HTTPS","La URL usa HTTP; los datos podrían viajar sin cifrado.")
    if source.username is not None or source.password is not None:
        add(25,"high","Credenciales antes del dominio","La información antes de @ puede ocultar el host real.")
    try: ipaddress.ip_address(host.strip("[]")); add(20,"medium","El host es una dirección IP","Verifica el origen; algunas webs legítimas también usan IPs.")
    except ValueError: pass
    if host.startswith("xn--") or ".xn--" in host:
        add(20,"medium","Dominio internacionalizado (punycode)","Puede ser legítimo, pero también se usa para imitar dominios.")
    if host in SHORTENERS: add(15,"medium","Acortador de enlaces","El destino no se ve directamente; confirma el origen.")
    lowered=(host+p.path+"?"+p.query).lower()
    matched=sorted(w for w in WORDS if w in lowered)
    if matched: add(min(20,5+3*len(matched)),"medium","Palabras frecuentes en señuelos","Términos detectados: "+", ".join(matched)+". No demuestran fraude por sí solos.")
    bait=sorted(b for b in BRANDS if b in host and host != b+".com")
    if bait: add(20,"high","Posible mención de marca en otro dominio","El host menciona "+", ".join(bait)+"; verifica el dominio oficial.")
    if len(host)>45: add(10,"low","Dominio largo","Comprueba cada parte del nombre del dominio.")
    if HEX.search(p.path+p.query): add(5,"low","Caracteres codificados en la URL","La codificación es común, pero puede dificultar la lectura.")
    if not findings: findings.append({"level":"info","title":"No se detectaron señales heurísticas comunes","detail":"Esto no demuestra que el enlace sea seguro. No se consultó reputación externa."})
    score=min(score,100)
    if score>=50: risk,label,advice="high","Riesgo elevado","No introduzcas contraseñas ni datos de pago. Verifica el remitente por otro canal."
    elif score>=20: risk,label,advice="medium","Precaución","Revisa el dominio y confirma el origen antes de continuar."
    else: risk,label,advice="low","Pocas señales detectadas","No se detectaron muchas señales heurísticas; el enlace no está certificado como seguro."
    return {"input_url":raw,"normalized_url":normalized,"hostname":host,"risk":risk,"risk_label":label,"score":score,"score_type":"heuristic_indicator_score_not_probability","findings":findings,"advice":advice,"limitations":["No se ha abierto ni visitado el enlace.","No se ha consultado ninguna fuente externa de reputación.","La puntuación no es una probabilidad y puede producir falsos positivos o negativos.","La ausencia de señales detectadas no garantiza que el enlace sea seguro."]}

@app.get("/api/health")
def health(): return {"status":"ok","product":"ZettaCore Sentinel","version":"0.1.0"}

@app.post("/api/analyze")
def analyze_url(payload:AnalyzeRequest):
    try: return analyze(payload.url)
    except ValueError as e: raise HTTPException(status_code=422,detail=str(e)) from e

@app.get("/",response_class=HTMLResponse)
def home():
    with open("app/static/index.html",encoding="utf-8") as f: return f.read()
