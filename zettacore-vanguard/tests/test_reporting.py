from pathlib import Path

import pytest

reportlab = pytest.importorskip("reportlab")
from pypdf import PdfReader

from vanguard.reporting import generate_vulnerability_report


def test_generates_trilingual_pdf_report(tmp_path: Path) -> None:
    record = {
        "cve_id": "CVE-2025-12345", "description": "A sample vulnerability <script>alert(1)</script>",
        "published": "2025-01-01", "last_modified": "2025-01-02", "cvss_score": 8.8,
        "cvss_severity": "HIGH", "source": "NIST NVD", "retrieved_at": "2025-01-03T00:00:00+00:00",
        "known_exploited": 1,
    }
    for language in ("en", "es", "pt-BR"):
        path = generate_vulnerability_report(tmp_path / f"report-{language}.pdf", [record], language=language)
        assert path.exists() and path.stat().st_size > 500
        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        assert "CVE-2025-12345" in text
        assert "CISA KEV" in text
        assert "script" in text


def test_empty_report_and_invalid_language(tmp_path: Path) -> None:
    path = generate_vulnerability_report(tmp_path / "empty.pdf", [], language="es")
    assert path.exists()
    with pytest.raises(ValueError, match="Language"):
        generate_vulnerability_report(tmp_path / "bad.pdf", [], language="fr")
