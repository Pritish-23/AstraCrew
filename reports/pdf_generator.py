"""
AstraCrew: Executive Dossier PDF Generator
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

from schemas.models import AstraCrewAuditReport


class AstraPDFReportGenerator:
    """Renders an AstraCrewAuditReport into a clean, multi-page security audit PDF."""

    @staticmethod
    def build_pdf(report: AstraCrewAuditReport, output_path: str) -> None:
        doc = SimpleDocTemplate(
            output_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle", parent=styles["Heading1"], fontSize=22, leading=26, textColor=colors.HexColor("#0F172A")
        )
        h2_style = ParagraphStyle(
            "Heading2", parent=styles["Heading2"], fontSize=13, leading=17,
            textColor=colors.HexColor("#1E293B"), spaceBefore=12, spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "Body", parent=styles["Normal"], fontSize=9.5, leading=13.5, textColor=colors.HexColor("#334155")
        )
        code_style = ParagraphStyle(
            "DiffCode", parent=styles["Code"], fontSize=7.5, leading=9.5,
            textColor=colors.HexColor("#0F172A"), backColor=colors.HexColor("#F1F5F9"),
        )

        elements = [
            Paragraph("AstraCrew: AI Security & Guardrail Audit Report", title_style),
            Paragraph(
                f"<b>Target Suite:</b> {report.target_name} | <b>Mode:</b> {report.execution_mode} | "
                f"<b>Timestamp:</b> {report.timestamp}",
                body_style,
            ),
            Spacer(1, 14),
        ]

        kpi_data = [
            ["Security Benchmark Metric", "Observed Audit Result"],
            ["Mathematical Resilience Index", f"{report.resilience_score:.1f} / 100.0"],
            ["Breach Rate Percentage", f"{report.breach_rate_pct:.1f}%"],
            ["Total Adversarial Probes Run", str(report.total_probes_run)],
            ["Confirmed Boundary Breaches", str(report.total_breaches)],
        ]
        kpi_table = Table(kpi_data, colWidths=[270, 270])
        kpi_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ]
            )
        )
        elements += [kpi_table, Spacer(1, 14), Paragraph("Executive Summary", h2_style),
                     Paragraph(report.executive_summary, body_style), Spacer(1, 10)]

        if report.category_breakdown:
            elements.append(Paragraph("OWASP Category Coverage", h2_style))
            cat_data = [["OWASP Category", "Probes Run", "Breaches"]]
            for cat, counts in sorted(report.category_breakdown.items()):
                cat_data.append([cat, str(counts.get("probes", 0)), str(counts.get("breaches", 0))])
            cat_table = Table(cat_data, colWidths=[300, 110, 110])
            cat_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ]
                )
            )
            elements += [cat_table, Spacer(1, 14)]

        elements.append(Paragraph("Adversarial Probes & Evaluation Verdicts", h2_style))
        findings_data = [["Probe ID", "Target", "OWASP Category", "Severity", "Breach?", "Gate"]]
        eval_map = {e.probe_id: e for e in report.evaluations}
        for probe in report.detailed_findings:
            e = eval_map.get(probe.probe_id)
            is_breached = "YES" if (e and e.breach_detected) else "NO"
            gate = e.gate_triggered if e else "NONE"
            findings_data.append(
                [probe.probe_id, probe.target_type, probe.owasp_category.split("-")[-1],
                 probe.severity_level, is_breached, gate]
            )
        findings_table = Table(findings_data, colWidths=[55, 55, 165, 60, 50, 145])
        findings_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ]
            )
        )
        elements += [findings_table, Spacer(1, 14), Paragraph("Automated Hardening Recommendations (Git Diff)", h2_style)]

        for rem in report.remediations:
            elements.append(Paragraph(f"<b>Target Vulnerability:</b> {rem.vulnerability_type}", body_style))
            elements.append(Paragraph(f"<b>Observed Failure:</b> {rem.observed_failure}", body_style))
            elements.append(Spacer(1, 4))
            elements.append(Preformatted(rem.suggested_prompt_patch, code_style))
            elements.append(Spacer(1, 10))

        doc.build(elements)