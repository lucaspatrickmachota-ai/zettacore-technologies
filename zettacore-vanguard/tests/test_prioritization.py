from vanguard.intelligence import VulnerabilityRecord
from vanguard.prioritization import assess_priority


def record(*, score: float | None, known_exploited: bool = False) -> VulnerabilityRecord:
    return VulnerabilityRecord(
        cve_id="CVE-2025-12345", description="Test record", published=None,
        last_modified=None, cvss_score=score, cvss_severity=None, source="NIST NVD",
        retrieved_at="2025-01-03T00:00:00+00:00", known_exploited=known_exploited,
    )


def test_known_exploited_vulnerability_is_highest_review_priority() -> None:
    assessment = assess_priority(record(score=4.2, known_exploited=True))
    assert assessment.priority == "P1"
    assert assessment.score == 75
    assert any("CISA" in reason for reason in assessment.rationale)
    assert "does not prove" in assessment.limitations


def test_cvss_bands_are_explainable() -> None:
    assert assess_priority(record(score=9.8)).priority == "P1"
    assert assess_priority(record(score=7.5)).priority == "P2"
    assert assess_priority(record(score=5.0)).priority == "P3"
    assert assess_priority(record(score=2.0)).priority == "P4"


def test_missing_cvss_does_not_invent_severity() -> None:
    assessment = assess_priority(record(score=None))
    assert assessment.priority == "P4"
    assert assessment.score == 0
    assert any("unknown" in reason for reason in assessment.rationale)
