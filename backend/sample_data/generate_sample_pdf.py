"""
Generates sample_deviation_report.pdf - a realistic manufacturing deviation
report used to demonstrate the DeviationIQ document-extraction tool.

Run with:  python generate_sample_pdf.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_PATH = Path(__file__).parent / "sample_deviation_report.pdf"

styles = getSampleStyleSheet()
navy = colors.HexColor("#1E2A4A")
grey = colors.HexColor("#5B6472")

title_style = ParagraphStyle(
    "TitleCustom", parent=styles["Heading1"], textColor=navy, fontSize=17, spaceAfter=2
)
subtitle_style = ParagraphStyle(
    "SubtitleCustom", parent=styles["Normal"], textColor=grey, fontSize=9, spaceAfter=10
)
section_style = ParagraphStyle(
    "SectionCustom",
    parent=styles["Heading3"],
    textColor=navy,
    fontSize=11,
    spaceBefore=14,
    spaceAfter=6,
)
body_style = ParagraphStyle("BodyCustom", parent=styles["Normal"], fontSize=10, leading=14)
label_style = ParagraphStyle("LabelCustom", parent=styles["Normal"], fontSize=9, textColor=grey)

doc = SimpleDocTemplate(
    str(OUT_PATH),
    pagesize=A4,
    topMargin=20 * mm,
    bottomMargin=20 * mm,
    leftMargin=20 * mm,
    rightMargin=20 * mm,
)

story = []

story.append(Paragraph("ARISTA BIOPHARMA LIMITED", title_style))
story.append(Paragraph("Quality Assurance Department &nbsp;|&nbsp; Manufacturing Deviation Report", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1, color=navy))
story.append(Spacer(1, 10))

meta_table = Table(
    [
        ["Deviation Reference", "DEV-2026-00738", "Date / Time", "09-Nov-2026, 09:20 IST"],
        ["Reported By", "Compression Operator", "Logged By", "QA Executive"],
    ],
    colWidths=[95, 140, 85, 140],
)
meta_table.setStyle(
    TableStyle(
        [
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), grey),
            ("TEXTCOLOR", (2, 0), (2, -1), grey),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
            ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]
    )
)
story.append(meta_table)

story.append(Paragraph("1. Site &amp; Process Details", section_style))
story.append(
    Paragraph(
        "<b>Manufacturing Site:</b> Arista Biopharma, Hyderabad Site<br/>"
        "<b>Area / Block:</b> Block C - Tablet Compression Suite<br/>"
        "<b>Process Step:</b> Tablet compression in-process weight control<br/>"
        "<b>Shift:</b> A Shift",
        body_style,
    )
)

story.append(Paragraph("2. Product &amp; Batch Details", section_style))
product_table = Table(
    [
        ["Product Name", "Losartan Potassium Tablets"],
        ["Product Strength / Grade", "50 mg"],
        ["Batch / Lot Number", "LST261109A"],
        ["Manufacturing Date", "09 November 2026"],
        ["Expiry Date", "October 2028"],
        ["Affected Quantity", "Approx. 18,500 compressed tablets"],
    ],
    colWidths=[200, 260],
)
product_table.setStyle(
    TableStyle(
        [
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#E5E7EB")),
        ]
    )
)
story.append(product_table)

story.append(Paragraph("3. Nature of Deviation", section_style))
story.append(
    Paragraph(
        "During routine in-process checks for batch LST261109A, the average tablet weight was observed "
        "at 262 mg for 20 consecutive tablets. The approved batch manufacturing record specifies a target "
        "tablet weight of 250 mg with an acceptable range of 242.5 mg to 257.5 mg. Compression was stopped "
        "at 09:20 IST, the tablets compressed since the previous acceptable check were segregated, and QA "
        "was informed for assessment.",
        body_style,
    )
)

story.append(Paragraph("4. Potential Impact &amp; Initial Severity", section_style))
story.append(
    Paragraph(
        "Potential impact includes tablet weight variation, possible assay variability, and risk of "
        "out-of-specification content uniformity if affected tablets proceed to coating and packing. No "
        "segregated tablets have been released to the next processing step. Initial severity is proposed "
        "as Major because an in-process control limit was exceeded for a commercial batch.",
        body_style,
    )
)

story.append(Spacer(1, 16))
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
story.append(Spacer(1, 6))
story.append(
    Paragraph(
        "This document was generated for demonstration purposes as part of the DeviationIQ "
        "document-extraction workflow.",
        label_style,
    )
)

doc.build(story)
print(f"Wrote {OUT_PATH}")
