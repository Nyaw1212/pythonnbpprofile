from __future__ import annotations

import base64
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .photo_service import get_drive_photo_data_url

GRID = colors.HexColor("#C8D2DC")
TEXT = colors.HexColor("#24313D")
MUTED = colors.HexColor("#687581")

THEMES = {
    "NBP": ("#1F6B45", "#155437", "#E7F2EB"),
    "MAX": ("#D97706", "#9A4D00", "#FFF0DD"),
    "MAXIMUM": ("#D97706", "#9A4D00", "#FFF0DD"),
    "MED": ("#2563A6", "#174B7E", "#E7F0FA"),
    "MEDIUM": ("#2563A6", "#174B7E", "#E7F0FA"),
    "MIN": ("#7A4B2A", "#5B351D", "#F2E9E2"),
    "MINIMUM": ("#7A4B2A", "#5B351D", "#F2E9E2"),
    "RDC": ("#D6A900", "#725800", "#FFF7CC"),
}


def _theme(person: dict[str, Any]):
    camp = str(person.get("camp") or "").strip().upper()
    main, ink, soft = THEMES.get(camp, ("#0B376D", "#0B2E5D", "#EAF1F8"))
    return colors.HexColor(main), colors.HexColor(ink), colors.HexColor(soft)


def _value(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    return text or "—"


def _full_name(person: dict[str, Any]) -> str:
    parts = [person.get("first_name"), person.get("middle_name"), person.get("last_name"), person.get("suffix")]
    return " ".join(str(part).strip() for part in parts if part and str(part).strip()) or "Unnamed Personnel"


def _parse_birthdate(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def _birthdate_text(value: Any) -> str:
    parsed = _parse_birthdate(value)
    return parsed.strftime("%B %d, %Y") if parsed else _value(value)


def _age(value: Any) -> str:
    born = _parse_birthdate(value)
    if not born:
        return "—"
    today = date.today()
    return str(today.year - born.year - ((today.month, today.day) < (born.month, born.day)))


def _home_address(person: dict[str, Any]) -> str:
    first = " ".join(filter(None, [str(person.get("address_no") or "").strip(), str(person.get("address_street") or "").strip()])).strip()
    barangay = str(person.get("address_barangay") or "").strip()
    city = str(person.get("address_city") or "").strip()
    province = str(person.get("address_province") or "").strip()
    zip_code = str(person.get("address_zip") or "").strip()
    parts = [part for part in (first, f"Brgy. {barangay}" if barangay else "", city, province) if part]
    text = ", ".join(parts)
    if zip_code:
        text = f"{text} {zip_code}".strip()
    return text or "—"


def _section_title(text: str, width: float, main_color) -> Table:
    table = Table([[text]], colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), main_color),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.3),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _info_table(rows: list[tuple[str, str]], width: float, soft_color, label_width: float = 30 * mm, compact: bool = True) -> Table:
    data = [[label, value] for label, value in rows]
    table = Table(data, colWidths=[label_width, width - label_width])
    pad = 4 if compact else 5
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("BACKGROUND", (0, 0), (0, -1), soft_color),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, -1), TEXT),
        ("FONTSIZE", (0, 0), (-1, -1), 7.4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]))
    return table


def _placeholder_table(headers: list[str], message: str, widths: list[float], main_color) -> Table:
    data = [headers, [message] + [""] * (len(headers) - 1)]
    table = Table(data, colWidths=widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), main_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 5.7),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("SPAN", (0, 1), (-1, 1)),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("TEXTCOLOR", (0, 1), (-1, 1), MUTED),
        ("FONTSIZE", (0, 1), (-1, 1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def _photo_flowable(person: dict[str, Any], width: float, height: float, soft_color, ink_color):
    badge = str(person.get("badge_number") or "photo")
    result = get_drive_photo_data_url(person.get("drive_file_id"), cache_key=badge)
    if result.get("ok") and result.get("data_url"):
        try:
            encoded = result["data_url"].split(",", 1)[1]
            image = Image(BytesIO(base64.b64decode(encoded)), width=width, height=height)
            image.hAlign = "CENTER"
            return image
        except Exception:
            pass
    initials = "".join((str(person.get(key) or "?").strip()[:1] for key in ("first_name", "last_name"))).upper()
    photo = Table([[initials]], colWidths=[width], rowHeights=[height])
    photo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), soft_color),
        ("BOX", (0, 0), (-1, -1), 0.8, ink_color),
        ("TEXTCOLOR", (0, 0), (-1, -1), ink_color),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 27),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return photo


def generate_profile_pdf(person: dict[str, Any], output_path: Path | str) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    main_color, ink_color, soft_color = _theme(person)

    page_width = 186 * mm
    left_width = 49 * mm
    gap = 5 * mm
    right_width = page_width - left_width - gap

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        rightMargin=12 * mm, leftMargin=12 * mm, topMargin=9 * mm, bottomMargin=8 * mm,
        title=f"Personnel Profile - {_full_name(person)}", author="NBP Personnel Lookup",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ProfileTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=22, textColor=ink_color, alignment=TA_CENTER, spaceAfter=0)
    subtitle_style = ParagraphStyle("ProfileSubtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=7.5, leading=9, textColor=ink_color, alignment=TA_CENTER)
    name_style = ParagraphStyle("Name", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=13, textColor=ink_color, alignment=TA_CENTER, spaceAfter=1 * mm)
    rank_style = ParagraphStyle("Rank", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=ink_color, alignment=TA_CENTER)

    story = [Paragraph("PERSONNEL PROFILE", title_style), Paragraph("PERSONNEL OFFICE & MOVEMENT TRACKING", subtitle_style), Spacer(1, 2.5 * mm)]
    rule = Table([[""]], colWidths=[page_width], rowHeights=[0.8 * mm])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), main_color)]))
    story.extend([rule, Spacer(1, 3.5 * mm)])

    photo = _photo_flowable(person, 43 * mm, 48 * mm, soft_color, ink_color)
    identity_rows = [
        ("Badge Number", _value(person.get("badge_number"))),
        ("ID Number", _value(person.get("id_number"))),
        ("Record ID", _value(person.get("record_id"))),
        ("Classification", _value(person.get("classification"))),
        ("Personnel Type", _value(person.get("personnel_type"))),
        ("Gender", _value(person.get("gender"))),
        ("Camp", _value(person.get("camp"))),
    ]
    personal_rows = [
        ("Birthdate", _birthdate_text(person.get("birthdate"))),
        ("Age", _age(person.get("birthdate"))),
        ("Civil Status", _value(person.get("civil_status"))),
        ("Religion", _value(person.get("religion"))),
        ("Highest Education", _value(person.get("highest_education"))),
        ("Home Address", _home_address(person)),
    ]
    emergency_rows = [
        ("Contact Person", _value(person.get("emergency_contact"))),
        ("Relationship", _value(person.get("emergency_relationship"))),
        ("Contact Number", _value(person.get("emergency_number"))),
        ("Address", _value(person.get("emergency_address"))),
    ]

    left_block = [photo, Spacer(1, 2 * mm), Paragraph(_full_name(person).upper(), name_style), Paragraph(_value(person.get("rank")), rank_style), Spacer(1, 2 * mm), _info_table(identity_rows, left_width - 2 * mm, soft_color, 21 * mm)]
    left_block += [Spacer(1, 2.5 * mm), _section_title("PERSONAL INFORMATION", left_width - 2 * mm, main_color), _info_table(personal_rows, left_width - 2 * mm, soft_color, 20 * mm)]
    left_block += [Spacer(1, 2.5 * mm), _section_title("EMERGENCY CONTACT", left_width - 2 * mm, main_color), _info_table(emergency_rows, left_width - 2 * mm, soft_color, 20 * mm)]

    current_rows = [("Office", _value(person.get("office"))), ("Camp", _value(person.get("camp"))), ("Rank", _value(person.get("rank"))), ("Status", "CURRENT")]
    right_block = [
        _section_title("CURRENT OFFICE INFORMATION", right_width, main_color),
        _info_table(current_rows, right_width, soft_color, 30 * mm),
        Spacer(1, 3 * mm),
        _section_title("OFFICE MOVEMENT HISTORY", right_width, main_color),
        _placeholder_table(["#", "From Office", "To Office", "Position", "From Date", "To Date", "Remarks"], "No office movement records yet.", [6*mm,22*mm,22*mm,22*mm,16*mm,16*mm,right_width-104*mm], main_color),
        Spacer(1, 3 * mm),
        _section_title("MEMO RECEIVED", right_width, main_color),
        _placeholder_table(["Date Received", "Memo No.", "Subject / Description", "From"], "No memo records yet.", [24*mm,24*mm,55*mm,right_width-103*mm], main_color),
        Spacer(1, 3 * mm),
        _section_title("COMMENDATIONS / RECOGNITIONS", right_width, main_color),
        _placeholder_table(["Date Received", "Award / Title", "Presented By", "Remarks"], "No commendation records yet.", [24*mm,40*mm,32*mm,right_width-96*mm], main_color),
        Spacer(1, 3 * mm),
        _section_title("REMARKS", right_width, main_color),
    ]
    remarks = Table([["No remarks recorded."]], colWidths=[right_width], rowHeights=[12 * mm])
    remarks.setStyle(TableStyle([("BOX", (0,0), (-1,-1), .4, GRID), ("TEXTCOLOR",(0,0),(-1,-1),MUTED), ("FONTSIZE",(0,0),(-1,-1),7), ("VALIGN",(0,0),(-1,-1),"TOP"), ("LEFTPADDING",(0,0),(-1,-1),6), ("TOPPADDING",(0,0),(-1,-1),5)]))
    right_block.append(remarks)

    top = Table([[left_block, "", right_block]], colWidths=[left_width, gap, right_width], hAlign="LEFT")
    top.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0), ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ("LINEAFTER", (0,0), (0,0), .45, GRID),
    ]))
    story.extend([top, Spacer(1, 3 * mm)])

    generated = datetime.now().strftime("%B %d, %Y %I:%M %p")
    footer = Table([["PREPARED BY: ____________________", f"DATE GENERATED: {generated}"]], colWidths=[93*mm,93*mm])
    footer.setStyle(TableStyle([("LINEABOVE",(0,0),(-1,0),.4,GRID), ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),6.5), ("TEXTCOLOR",(0,0),(-1,-1),ink_color), ("ALIGN",(1,0),(1,0),"RIGHT"), ("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(KeepTogether(footer))

    doc.build(story)
    return output_path
