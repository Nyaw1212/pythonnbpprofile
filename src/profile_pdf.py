from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#0B2E5D")
GOLD = colors.HexColor("#D9A522")
LIGHT_BLUE = colors.HexColor("#EEF3F7")
GRID = colors.HexColor("#C8D2DC")
TEXT = colors.HexColor("#24313D")
MUTED = colors.HexColor("#687581")
GREEN_BG = colors.HexColor("#DFF3DF")
GREEN = colors.HexColor("#23743A")


def _value(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    return text or "-"


def _full_name(person: dict[str, Any]) -> str:
    parts = [person.get("first_name"), person.get("middle_name"), person.get("last_name"), person.get("suffix")]
    return " ".join(str(part).strip() for part in parts if part and str(part).strip()) or "Unnamed Personnel"


def _section_title(text: str) -> Table:
    table = Table([[text]], colWidths=[178 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _info_table(rows: list[tuple[str, str]], width: float) -> Table:
    data = [[label, value] for label, value in rows]
    table = Table(data, colWidths=[42 * mm, width - 42 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, -1), TEXT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _placeholder_table(headers: list[str], message: str, widths: list[float]) -> Table:
    data = [headers, [message] + [""] * (len(headers) - 1)]
    table = Table(data, colWidths=widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 6.5),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("SPAN", (0, 1), (-1, 1)),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("TEXTCOLOR", (0, 1), (-1, 1), MUTED),
        ("FONTSIZE", (0, 1), (-1, 1), 8),
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def generate_profile_pdf(person: dict[str, Any], output_path: Path | str) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"Personnel Profile - {_full_name(person)}",
        author="NBP Personnel Lookup",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ProfileTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=27,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=1 * mm,
    )
    subtitle_style = ParagraphStyle(
        "ProfileSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10,
        textColor=NAVY,
        alignment=TA_CENTER,
    )
    name_style = ParagraphStyle(
        "Name",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=15,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=2 * mm,
    )
    rank_style = ParagraphStyle(
        "Rank",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=MUTED,
        alignment=TA_CENTER,
    )

    story = []
    story.append(Paragraph("PERSONNEL PROFILE", title_style))
    story.append(Paragraph("NEW BILIBID PRISON - PERSONNEL OFFICE & MOVEMENT TRACKING", subtitle_style))
    story.append(Spacer(1, 3 * mm))
    rule = Table([[""]], colWidths=[178 * mm], rowHeights=[1.2 * mm])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY)]))
    story.append(rule)
    story.append(Spacer(1, 5 * mm))

    initials = "".join((str(person.get(key) or "?").strip()[:1] for key in ("first_name", "last_name"))).upper()
    photo = Table([[initials]], colWidths=[46 * mm], rowHeights=[54 * mm])
    photo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 0.8, NAVY),
        ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 28),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    identity_rows = [
        ("Badge Number", _value(person.get("badge_number"))),
        ("Record ID", _value(person.get("record_id"))),
        ("Classification", _value(person.get("classification"))),
        ("Personnel Type", _value(person.get("personnel_type"))),
        ("Gender", _value(person.get("gender"))),
        ("Camp", _value(person.get("camp"))),
    ]
    identity_info = _info_table(identity_rows, 56 * mm)
    identity_block = [
        photo,
        Spacer(1, 3 * mm),
        Paragraph(_full_name(person).upper(), name_style),
        Paragraph(_value(person.get("rank")), rank_style),
        Spacer(1, 3 * mm),
        identity_info,
    ]

    current_rows = [
        ("Office", _value(person.get("office"))),
        ("Camp", _value(person.get("camp"))),
        ("Rank", _value(person.get("rank"))),
        ("Status", "CURRENT"),
    ]
    current = [_section_title("CURRENT OFFICE INFORMATION"), _info_table(current_rows, 116 * mm)]

    movement = [
        Spacer(1, 4 * mm),
        _section_title("OFFICE MOVEMENT HISTORY"),
        _placeholder_table(
            ["#", "From Office", "To Office", "Position", "From Date", "To Date", "Remarks"],
            "No office movement records yet.",
            [7 * mm, 23 * mm, 23 * mm, 23 * mm, 15 * mm, 15 * mm, 25 * mm],
        ),
    ]

    right_block = current + movement
    top = Table([[identity_block, right_block]], colWidths=[58 * mm, 120 * mm], hAlign="LEFT")
    top.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 4 * mm),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(top)
    story.append(Spacer(1, 5 * mm))

    memo = [_section_title("MEMO RECEIVED"), _placeholder_table(["Date Received", "Memo No.", "Subject / Description", "From"], "No memo records yet.", [24 * mm, 28 * mm, 45 * mm, 30 * mm])]
    comm = [_section_title("COMMENDATIONS / RECOGNITIONS"), _placeholder_table(["Date Received", "Award / Title", "Presented By", "Remarks"], "No commendation records yet.", [24 * mm, 36 * mm, 31 * mm, 36 * mm])]
    lower = Table([[memo, comm]], colWidths=[87 * mm, 87 * mm])
    lower.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 2 * mm),
        ("LEFTPADDING", (1, 0), (1, 0), 2 * mm),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(lower)
    story.append(Spacer(1, 5 * mm))

    story.append(_section_title("REMARKS"))
    remarks = Table([["No remarks recorded."]], colWidths=[178 * mm], rowHeights=[20 * mm])
    remarks.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.45, GRID),
        ("TEXTCOLOR", (0, 0), (-1, -1), MUTED),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(remarks)
    story.append(Spacer(1, 5 * mm))

    generated = datetime.now().strftime("%B %d, %Y %I:%M %p")
    footer = Table([["PREPARED BY: ____________________", f"DATE GENERATED: {generated}"]], colWidths=[89 * mm, 89 * mm])
    footer.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(KeepTogether(footer))

    doc.build(story)
    return output_path
