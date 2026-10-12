"""PDF reporting for public vulnerability intelligence and local inventory."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vanguard.prioritization import assess_priority


def generate_vulnerability_report(
    output_path: str | Path,
    records: list[dict[str, Any]],
    *,
    language: str = "en",
    title: str | None = None,
) -> Path:
    """Generate a PDF report; records are public metadata, not confirmed asset findings."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as error:
        raise RuntimeError("PDF reporting requires the optional dependency: pip install -e '.[reports]'") from error

    translations = {
        "en": {
            "title": "ZettaCore Vanguard — Vulnerability Intelligence Report",
            "subtitle": "Public vulnerability metadata; not proof that an asset is affected or compromised.",
            "generated": "Generated (UTC)", "count": "Records included", "cve": "CVE ID",
            "priority": "Triage", "cvss": "CVSS", "kev": "CISA KEV", "yes": "Yes", "no": "No",
            "description": "Description", "source": "Source / retrieved", "rationale": "Triage rationale",
            "limitations": "Limitations", "limit_text": "Priorities are a review heuristic, not an exploitation probability. Validate product/version and environment evidence before treating a CVE as applicable to an asset.",
            "empty": "No vulnerability records were provided. This report contains no findings.",
        },
        "es": {
            "title": "ZettaCore Vanguard — Informe de inteligencia de vulnerabilidades",
            "subtitle": "Metadatos públicos; no prueban que un activo esté afectado o comprometido.",
            "generated": "Generado (UTC)", "count": "Registros incluidos", "cve": "ID CVE",
            "priority": "Triaje", "cvss": "CVSS", "kev": "CISA KEV", "yes": "Sí", "no": "No",
            "description": "Descripción", "source": "Fuente / consulta", "rationale": "Motivo del triaje",
            "limitations": "Limitaciones", "limit_text": "Las prioridades son una heurística de revisión, no una probabilidad de explotación. Verifica producto, versión y evidencias del entorno antes de atribuir una CVE a un activo.",
            "empty": "No se proporcionaron registros de vulnerabilidades. Este informe no contiene hallazgos.",
        },
        "pt-BR": {
            "title": "ZettaCore Vanguard — Relatório de inteligência de vulnerabilidades",
            "subtitle": "Metadados públicos; não comprovam que um ativo esteja afetado ou comprometido.",
            "generated": "Gerado (UTC)", "count": "Registros incluídos", "cve": "ID CVE",
            "priority": "Triagem", "cvss": "CVSS", "kev": "CISA KEV", "yes": "Sim", "no": "Não",
            "description": "Descrição", "source": "Fonte / consulta", "rationale": "Motivo da triagem",
            "limitations": "Limitações", "limit_text": "As prioridades são uma heurística de revisão, não uma probabilidade de exploração. Valide produto, versão e evidências do ambiente antes de atribuir uma CVE a um ativo.",
            "empty": "Nenhum registro de vulnerabilidade foi fornecido. Este relatório não contém achados.",
        },
    }
    if language not in translations:
        raise ValueError("Language must be en, es, or pt-BR.")
    t = translations[language]
    destination = Path(output_path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="VanguardTitle", parent=styles["Title"], textColor=colors.HexColor("#101c2b"), alignment=TA_LEFT, fontSize=17, leading=22, spaceAfter=8))
    styles.add(ParagraphStyle(name="VanguardBody", parent=styles["BodyText"], fontSize=8, leading=11, spaceAfter=4, wordWrap="CJK"))
    styles.add(ParagraphStyle(name="VanguardSmall", parent=styles["BodyText"], fontSize=7, leading=9, wordWrap="CJK"))
    story = [Paragraph(title or t["title"], styles["VanguardTitle"]), Paragraph(t["subtitle"], styles["VanguardBody"]), Spacer(1, 3 * mm)]
    story.append(Paragraph(f"<b>{t['generated']}:</b> {datetime.now(timezone.utc).isoformat(timespec='seconds')} &nbsp;&nbsp; <b>{t['count']}:</b> {len(records)}", styles["VanguardBody"]))
    story.append(Spacer(1, 4 * mm))
    if not records:
        story.append(Paragraph(t["empty"], styles["VanguardBody"]))
    else:
        header = [t["cve"], t["priority"], t["cvss"], t["kev"], t["description"]]
        rows: list[list[Any]] = [header]
        for record in records:
            score = record.get("cvss_score")
            from vanguard.intelligence import VulnerabilityRecord
            vulnerability = VulnerabilityRecord(
                cve_id=str(record.get("cve_id", "Unknown")),
                description=str(record.get("description", "")),
                published=record.get("published"), last_modified=record.get("last_modified"),
                cvss_score=float(score) if isinstance(score, (int, float)) else None,
                cvss_severity=record.get("cvss_severity"), source=str(record.get("source", "Unknown")),
                retrieved_at=str(record.get("retrieved_at", "Unknown")),
                known_exploited=bool(record.get("known_exploited")),
            )
            assessment = assess_priority(vulnerability)
            description = str(record.get("description", "")) or "—"
            # ReportLab Paragraph escapes markup so source text cannot inject report formatting.
            from xml.sax.saxutils import escape
            rows.append([
                Paragraph(escape(vulnerability.cve_id), styles["VanguardSmall"]),
                Paragraph(escape(assessment.priority), styles["VanguardSmall"]),
                Paragraph(escape(str(score) if score is not None else "N/A"), styles["VanguardSmall"]),
                Paragraph(t["yes"] if vulnerability.known_exploited else t["no"], styles["VanguardSmall"]),
                Paragraph(escape(description), styles["VanguardSmall"]),
            ])
        table = Table(rows, colWidths=[24 * mm, 17 * mm, 15 * mm, 19 * mm, 100 * mm], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#101c2b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#c7d0d9")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f8")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([table, Spacer(1, 5 * mm)])
        for record in records:
            from vanguard.intelligence import VulnerabilityRecord
            vulnerability = VulnerabilityRecord(
                cve_id=str(record.get("cve_id", "Unknown")), description=str(record.get("description", "")),
                published=record.get("published"), last_modified=record.get("last_modified"),
                cvss_score=float(record["cvss_score"]) if isinstance(record.get("cvss_score"), (int, float)) else None,
                cvss_severity=record.get("cvss_severity"), source=str(record.get("source", "Unknown")),
                retrieved_at=str(record.get("retrieved_at", "Unknown")), known_exploited=bool(record.get("known_exploited")),
            )
            assessment = assess_priority(vulnerability)
            story.append(Paragraph(f"<b>{escape(vulnerability.cve_id)} — {t['rationale']}</b>", styles["VanguardBody"]))
            for reason in assessment.rationale:
                story.append(Paragraph("• " + escape(reason), styles["VanguardSmall"]))
            story.append(Paragraph(f"<b>{t['source']}:</b> {escape(vulnerability.source)} / {escape(vulnerability.retrieved_at)}", styles["VanguardSmall"]))
            story.append(Spacer(1, 2 * mm))
    story.extend([Spacer(1, 4 * mm), Paragraph(f"<b>{t['limitations']}</b> {t['limit_text']}", styles["VanguardBody"])])
    document = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=14 * mm, leftMargin=14 * mm, topMargin=14 * mm, bottomMargin=14 * mm, title=title or t["title"], author="ZettaCore Technologies")
    document.build(story)
    return destination
