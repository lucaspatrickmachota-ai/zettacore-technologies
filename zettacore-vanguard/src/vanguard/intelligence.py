"""Read-only connectors for public CVE and CISA KEV intelligence.

This module imports public vulnerability metadata only. It does not scan assets,
prove exploitation in a customer's environment, or execute downloaded content.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

NVD_CVE_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CISA_KEV_CATALOG = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
USER_AGENT = "ZettaCore-Vanguard/0.1 (public vulnerability intelligence; contact via project repository)"
DEFAULT_TIMEOUT_SECONDS = 12
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class IntelligenceSourceError(RuntimeError):
    """Raised when a public intelligence source cannot be read or parsed."""


@dataclass(frozen=True, slots=True)
class VulnerabilityRecord:
    cve_id: str
    description: str
    published: str | None
    last_modified: str | None
    cvss_score: float | None
    cvss_severity: str | None
    source: str
    retrieved_at: str
    known_exploited: bool = False
    kev_date_added: str | None = None
    kev_due_date: str | None = None
    kev_required_action: str | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_iso(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _cvss(metrics: object) -> tuple[float | None, str | None]:
    """Return the first available CVSS score/severity, preferring v4, v3.1, v3.0, v2."""
    if not isinstance(metrics, dict):
        return None, None
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            data = entry.get("cvssData")
            if not isinstance(data, dict):
                continue
            score = data.get("baseScore")
            severity = data.get("baseSeverity") or entry.get("baseSeverity")
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                clean_severity = severity.strip().upper() if isinstance(severity, str) else None
                return float(score), clean_severity
    return None, None


def parse_nvd_payload(payload: object, *, retrieved_at: str | None = None) -> list[VulnerabilityRecord]:
    """Normalize an NVD CVE API v2 response without inventing missing fields."""
    if not isinstance(payload, dict):
        raise IntelligenceSourceError("NVD response must be a JSON object.")
    vulnerabilities = payload.get("vulnerabilities")
    if not isinstance(vulnerabilities, list):
        raise IntelligenceSourceError("NVD response is missing its vulnerabilities list.")
    retrieved = retrieved_at or _utc_now()
    records: list[VulnerabilityRecord] = []
    for item in vulnerabilities:
        if not isinstance(item, dict) or not isinstance(item.get("cve"), dict):
            continue
        cve = item["cve"]
        cve_id = cve.get("id")
        if not isinstance(cve_id, str) or not cve_id.startswith("CVE-"):
            continue
        descriptions = cve.get("descriptions", [])
        description = ""
        if isinstance(descriptions, list):
            english = next((entry for entry in descriptions if isinstance(entry, dict) and entry.get("lang") == "en" and isinstance(entry.get("value"), str)), None)
            any_text = next((entry for entry in descriptions if isinstance(entry, dict) and isinstance(entry.get("value"), str)), None)
            chosen = english or any_text
            if chosen:
                description = chosen["value"].strip()
        score, severity = _cvss(cve.get("metrics"))
        records.append(VulnerabilityRecord(
            cve_id=cve_id,
            description=description,
            published=_parse_iso(cve.get("published")),
            last_modified=_parse_iso(cve.get("lastModified")),
            cvss_score=score,
            cvss_severity=severity,
            source="NIST NVD",
            retrieved_at=retrieved,
        ))
    return records


def parse_kev_payload(payload: object) -> dict[str, dict[str, str | None]]:
    """Return CISA KEV metadata keyed by CVE ID, validating each catalog entry."""
    if not isinstance(payload, dict) or not isinstance(payload.get("vulnerabilities"), list):
        raise IntelligenceSourceError("CISA KEV response is missing its vulnerabilities list.")
    result: dict[str, dict[str, str | None]] = {}
    for item in payload["vulnerabilities"]:
        if not isinstance(item, dict):
            continue
        cve_id = item.get("cveID")
        if not isinstance(cve_id, str) or not cve_id.startswith("CVE-"):
            continue
        result[cve_id] = {
            "date_added": _parse_iso(item.get("dateAdded")),
            "due_date": _parse_iso(item.get("dueDate")),
            "required_action": _parse_iso(item.get("requiredAction")),
            "vendor_project": _parse_iso(item.get("vendorProject")),
            "product": _parse_iso(item.get("product")),
            "vulnerability_name": _parse_iso(item.get("vulnerabilityName")),
        }
    return result


def fetch_json(url: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> object:
    """Fetch JSON from a connector-owned URL with a timeout and response-size cap."""
    if url not in (CISA_KEV_CATALOG,) and not url.startswith(NVD_CVE_API + "?"):
        raise ValueError("Only the configured NVD and CISA KEV endpoints are permitted.")
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                raise IntelligenceSourceError("Intelligence response exceeds the configured size limit.")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise IntelligenceSourceError(f"Public intelligence source unavailable: {error}") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise IntelligenceSourceError("Intelligence response exceeds the configured size limit.")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IntelligenceSourceError("Intelligence source returned invalid JSON.") from error


def fetch_cve(cve_id: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> list[VulnerabilityRecord]:
    """Retrieve one CVE by identifier from the official NVD CVE API v2."""
    normalized = cve_id.strip().upper()
    if len(normalized) > 32 or not normalized.startswith("CVE-") or not all(part.isdigit() for part in normalized[4:].split("-")) or len(normalized.split("-")) != 3:
        raise ValueError("Enter a CVE identifier such as CVE-2024-12345.")
    url = NVD_CVE_API + "?" + urlencode({"cveId": normalized})
    payload = fetch_json(url, timeout=timeout)
    records = parse_nvd_payload(payload)
    return [record for record in records if record.cve_id == normalized]


def fetch_kev_catalog(*, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, dict[str, str | None]]:
    """Download and normalize the public CISA Known Exploited Vulnerabilities catalog."""
    return parse_kev_payload(fetch_json(CISA_KEV_CATALOG, timeout=timeout))


def enrich_with_kev(
    records: list[VulnerabilityRecord],
    catalog: dict[str, dict[str, str | None]],
) -> list[VulnerabilityRecord]:
    """Attach KEV status to CVE records; KEV membership is not proof of local compromise."""
    enriched: list[VulnerabilityRecord] = []
    for record in records:
        kev = catalog.get(record.cve_id)
        enriched.append(VulnerabilityRecord(
            cve_id=record.cve_id,
            description=record.description,
            published=record.published,
            last_modified=record.last_modified,
            cvss_score=record.cvss_score,
            cvss_severity=record.cvss_severity,
            source=record.source,
            retrieved_at=record.retrieved_at,
            known_exploited=kev is not None,
            kev_date_added=kev.get("date_added") if kev else None,
            kev_due_date=kev.get("due_date") if kev else None,
            kev_required_action=kev.get("required_action") if kev else None,
        ))
    return enriched
