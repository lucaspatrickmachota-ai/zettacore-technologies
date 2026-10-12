from vanguard.intelligence import (
    IntelligenceSourceError,
    VulnerabilityRecord,
    enrich_with_kev,
    parse_kev_payload,
    parse_nvd_payload,
)


def test_parse_nvd_cve_and_cvss_metadata() -> None:
    payload = {
        "vulnerabilities": [{"cve": {
            "id": "CVE-2025-12345",
            "published": "2025-01-01T00:00:00.000",
            "lastModified": "2025-01-02T00:00:00.000",
            "descriptions": [
                {"lang": "fr", "value": "Description française"},
                {"lang": "en", "value": "Test vulnerability description"},
            ],
            "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 8.8, "baseSeverity": "HIGH"}}]},
        }}]
    }
    records = parse_nvd_payload(payload, retrieved_at="2025-01-03T00:00:00+00:00")
    assert len(records) == 1
    assert records[0].cve_id == "CVE-2025-12345"
    assert records[0].description == "Test vulnerability description"
    assert records[0].cvss_score == 8.8
    assert records[0].cvss_severity == "HIGH"
    assert records[0].source == "NIST NVD"


def test_parse_kev_catalog_and_enrich_without_claiming_compromise() -> None:
    catalog = parse_kev_payload({"vulnerabilities": [{
        "cveID": "CVE-2025-12345", "dateAdded": "2025-01-01", "dueDate": "2025-01-15",
        "requiredAction": "Apply vendor mitigations.", "vendorProject": "Example", "product": "Server",
        "vulnerabilityName": "Example flaw",
    }]})
    record = VulnerabilityRecord(
        cve_id="CVE-2025-12345", description="Example", published=None, last_modified=None,
        cvss_score=8.8, cvss_severity="HIGH", source="NIST NVD",
        retrieved_at="2025-01-03T00:00:00+00:00",
    )
    enriched = enrich_with_kev([record], catalog)[0]
    assert enriched.known_exploited is True
    assert enriched.kev_date_added == "2025-01-01"
    assert "compromised" not in enriched.description.lower()
    assert enrich_with_kev([record], {})[0].known_exploited is False


def test_malformed_sources_raise_clear_errors() -> None:
    for parser, payload in ((parse_nvd_payload, []), (parse_kev_payload, {})):
        try:
            parser(payload)
        except IntelligenceSourceError:
            pass
        else:
            raise AssertionError("Malformed source payload should be rejected")
