from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io

STATUS_COLORS = {
    "COMPLIANT": colors.HexColor("#15803D"),
    "NON_COMPLIANT": colors.HexColor("#B91C1C"),
    "REVIEW_REQUIRED": colors.HexColor("#B45309"),
}


def build_report_pdf(inspection: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Heading1"], fontSize=18,
                                  textColor=colors.HexColor("#0F1B2D"), spaceAfter=2)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=9,
                                textColor=colors.HexColor("#5B6472"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12,
                         textColor=colors.HexColor("#0F1B2D"), spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13)

    story = []
    story.append(Paragraph("MetriSure Inspection Report", title_style))
    story.append(Paragraph("Legal Metrology Compliance Platform &mdash; Automated Screening Report", sub_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#D9DEE6"), thickness=1))
    story.append(Spacer(1, 10))

    meta_table = Table([
        ["Inspection ID", f"#{inspection['id']}"],
        ["Product", inspection.get("product_name") or "Unidentified product"],
        ["Date/Time (UTC)", inspection["created_at"]],
        ["OCR Confidence", f"{round(inspection['ocr_confidence']*100)}%"],
    ], colWidths=[45 * mm, 120 * mm])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#5B6472")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    status = inspection["status"]
    status_color = STATUS_COLORS.get(status, colors.grey)
    score_table = Table([[f"Compliance Score: {inspection['score']}%",
                           status.replace("_", " ")]], colWidths=[90 * mm, 75 * mm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
        ("TEXTCOLOR", (1, 0), (1, 0), status_color),
        ("FONTSIZE", (0, 0), (-1, -1), 13),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Rule-by-Rule Evaluation", h2))
    rule_rows = [["Rule", "Requirement", "Sev.", "Result", "Extracted Value"]]
    for r in inspection["rule_results"]:
        rule_rows.append([
            r["rule_code"], r["label"][:40] + ("…" if len(r["label"]) > 40 else ""),
            r["severity"], r["outcome"], (r["extracted_value"] or "—")[:28]
        ])
    rt = Table(rule_rows, colWidths=[16 * mm, 62 * mm, 14 * mm, 22 * mm, 51 * mm], repeatRows=1)
    outcome_colors = {"PASS": colors.HexColor("#15803D"), "FAIL": colors.HexColor("#B91C1C"),
                       "REVIEW": colors.HexColor("#B45309")}
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F1B2D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.3),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9DEE6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F8FA")]),
    ]
    for i, r in enumerate(inspection["rule_results"], start=1):
        style_cmds.append(("TEXTCOLOR", (3, i), (3, i), outcome_colors.get(r["outcome"], colors.black)))
        style_cmds.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))
    rt.setStyle(TableStyle(style_cmds))
    story.append(rt)
    story.append(Spacer(1, 14))

    failed = [r for r in inspection["rule_results"] if r["outcome"] in ("FAIL", "REVIEW")]
    if failed:
        story.append(Paragraph("Potential Issues &amp; Explanations", h2))
        for r in failed:
            tag = "REQUIRES OFFICER REVIEW" if r["outcome"] == "REVIEW" else "VIOLATION"
            story.append(Paragraph(f"<b>[{r['rule_code']}] {tag}:</b> {r['message'] or r['label']}", body))
            story.append(Spacer(1, 3))
    else:
        story.append(Paragraph("No violations detected. All mandatory declarations were found and validated.", body))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#D9DEE6"), thickness=1))
    story.append(Spacer(1, 6))
    disclaimer = ParagraphStyle("Disc", parent=styles["Normal"], fontSize=7.8, textColor=colors.HexColor("#8A93A3"))
    story.append(Paragraph(
        "This report is generated by an automated preliminary compliance screening system. "
        "AI/OCR is used only to extract and normalize label information; all compliance decisions "
        "are made by a deterministic, versioned rule engine. This is decision support, not a final "
        "legal determination &mdash; final enforcement determination remains with the competent authority.",
        disclaimer
    ))

    doc.build(story)
    return buf.getvalue()
