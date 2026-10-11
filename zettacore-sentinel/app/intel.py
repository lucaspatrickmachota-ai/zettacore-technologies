from __future__ import annotations

import os

import httpx

URLHAUS_URL_QUERY_ENDPOINT = "https://urlhaus-api.abuse.ch/v1/url/"


async def lookup_urlhaus(url: str) -> dict:
    """Optional reputation lookup. Caller must obtain explicit user consent.

    The URLhaus key and licence acknowledgement stay server-side. No URL is sent
    unless both are configured and the caller explicitly opts in.
    """
    api_key = os.getenv("URLHAUS_AUTH_KEY", "").strip()
    if not api_key:
        return {
            "provider": "URLhaus",
            "status": "not_configured",
            "checked": False,
            "summary": "La consulta externa no está configurada en el servidor.",
        }
    if os.getenv("URLHAUS_LICENSE_APPROVED", "").strip().lower() != "true":
        return {
            "provider": "URLhaus",
            "status": "license_not_confirmed",
            "checked": False,
            "summary": "La consulta externa está desactivada hasta confirmar una licencia compatible con el uso previsto.",
        }

    try:
        timeout = httpx.Timeout(5.0, connect=2.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await client.post(
                URLHAUS_URL_QUERY_ENDPOINT,
                headers={"Auth-Key": api_key},
                data={"url": url},
            )
            response.raise_for_status()
            data = response.json()
        query_status = data.get("query_status")
        if query_status == "ok":
            url_status = str(data.get("url_status", "unknown")).lower()
            entry_id = str(data.get("id", ""))
            reference = f"https://urlhaus.abuse.ch/url/{entry_id}/" if entry_id.isdigit() else None
            return {
                "provider": "URLhaus",
                "status": "listed",
                "checked": True,
                "summary": "La URL aparece en URLhaus, una fuente de indicadores relacionados con distribución de malware. Comprueba la vigencia del registro.",
                "threat": str(data.get("threat", "unknown"))[:80],
                "url_status": url_status if url_status in {"online", "offline", "unknown"} else "unknown",
                "date_added": str(data.get("date_added", ""))[:40],
                "reference": reference,
            }
        if query_status == "no_results":
            return {
                "provider": "URLhaus",
                "status": "no_match",
                "checked": True,
                "summary": "URLhaus no devolvió una coincidencia exacta. Esto no significa que el enlace sea seguro.",
            }
        return {
            "provider": "URLhaus",
            "status": "unavailable",
            "checked": False,
            "summary": "La fuente externa no pudo completar esta consulta.",
        }
    except (httpx.HTTPError, ValueError, TypeError):
        return {
            "provider": "URLhaus",
            "status": "unavailable",
            "checked": False,
            "summary": "La fuente externa no está disponible en este momento.",
        }
