"""Explainable prioritization for vulnerability intelligence (not exploit prediction)."""

from __future__ import annotations

from dataclasses import dataclass

from vanguard.intelligence import VulnerabilityRecord


@dataclass(frozen=True, slots=True)
class PriorityAssessment:
    priority: str
    score: int
    rationale: tuple[str, ...]
    limitations: str


def assess_priority(record: VulnerabilityRecord) -> PriorityAssessment:
    """Rank review urgency using only public metadata and explicit, auditable rules.

    This is a triage heuristic, not a probability of exploitation or proof that an
    asset is vulnerable/compromised. Asset-specific exposure and version evidence
    must be evaluated separately before a finding can be confirmed.
    """
    score = 0
    rationale: list[str] = []
    if record.known_exploited:
        score += 60
        rationale.append("Listed in the CISA Known Exploited Vulnerabilities catalog (+60).")
    if record.cvss_score is None:
        rationale.append("No CVSS base score was available; severity contribution is unknown.")
    elif record.cvss_score >= 9.0:
        score += 40
        rationale.append("CVSS base score is Critical (9.0–10.0) (+40).")
    elif record.cvss_score >= 7.0:
        score += 30
        rationale.append("CVSS base score is High (7.0–8.9) (+30).")
    elif record.cvss_score >= 4.0:
        score += 15
        rationale.append("CVSS base score is Medium (4.0–6.9) (+15).")
    elif record.cvss_score >= 0:
        score += 5
        rationale.append("CVSS base score is Low (0.0–3.9) (+5).")
    else:
        rationale.append("CVSS score is outside the expected range; no severity points applied.")

    if record.known_exploited or score >= 70:
        priority = "P1"
    elif score >= 30:
        priority = "P2"
    elif score >= 15:
        priority = "P3"
    else:
        priority = "P4"
    return PriorityAssessment(
        priority=priority,
        score=score,
        rationale=tuple(rationale),
        limitations=(
            "Triage score only. It is not a probability of exploitation and does not prove "
            "the asset is affected or compromised. Confirm product/version, exposure, and "
            "environmental context before treating this as an asset finding."
        ),
    )
