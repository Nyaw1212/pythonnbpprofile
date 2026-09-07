from __future__ import annotations

import base64
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

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
    "MAX": ("#D97706", "#9A4D00", "#FFF0DD"), "MAXIMUM": ("#D97706", "#9A4D00", "#FFF0DD"),
    "MED": ("#2563A6", "#174B7E", "#E7F0FA"), "MEDIUM": ("#2563A6", "#174B7E", "#E7F0FA"),
    "MIN": ("#7A4B2A", "#5B351D", "#F2E9E2"), "MINIMUM": ("#7A4B2A", "#5B351D", "#F2E9E2"),
    "RDC": ("#D6A900", "#725800", "#FFF7CC"),
}

def _theme(person):
    main, ink, soft = THEMES.get(str(person.get("camp") or "").strip().upper(), ("#0B376D", "#0B2E5D", "#EAF1F8"))
    return colors.HexColor(main), colors.HexColor(ink), colors.HexColor(soft)

def _value(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    return text or "—"

def _full_name(person) -> str:
    parts = [person.get("first_name"), person.get("middle_name"), person.get("last_name"), person.get("suffix")]
    return " ".join(str(x).strip() for x in parts if x and str(x).strip()) or "Unnamed Personnel"

def _parse_birthdate(value):
    if not value: return None
    if isinstance(value, datetime): return value.date()
    if isinstance(value, date): return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y"):
        try: return datetime.strptime(text, fmt).date()
        except ValueError: pass
    return None

def _birthdate_text(value):
    parsed = _parse_birthdate(value)
    return parsed.strftime("%B %d, %Y") if parsed else _value(value)

def _age(value):
    born = _parse_birthdate(value)
    if not born: return "—"
    today = date.today()
    return str(today.year - born.year - ((today.month, today.day) < (born.month, born.day)))

def _home_address(person):
    first = " ".join(filter(None, [str(person.get("address_no") or "").strip(), str(person.get("address_street") or "").strip()])).strip()
    barangay = str(person.get("address_barangay") or "").strip()
    city = str(person.get("address_city") or "").strip()
    province = str(person.get("address_province") or "").strip()
    zip_code = str(person.get("address_zip") or "").strip()
    parts = [x for x in (first, f"Brgy. {barangay}" if barangay else "", city, province) if x]
    text = ", ".join(parts)
    return (f"{text} {zip_code}".strip() if zip_code else text) or "—"

def _p(value, bold=False, size=6.5):
    style = ParagraphStyle("p", fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size, leading=size+1.2, textColor=TEXT, wordWrap="CJK", splitLongWords=True)
    return Paragraph(escape(_value(value)), style)

def _section_title(text, width, main):
    t = Table([[text]], colWidths=[width])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),main),("TEXTCOLOR",(0,0),(-1,-1),colors.white),("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),7.7),("LEFTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    return t

def _info_table(rows, width, soft, label_width=19*mm):
    data = [[_p(label, True, 5.8), _p(value, False, 6.1)] for label, value in rows]
    t = Table(data, colWidths=[label_width, width-label_width])
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.35,GRID),("BACKGROUND",(0,0),(0,-1),soft),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),("TOPPADDING",(0,0),(-1,-1),2.5),("BOTTOMPADDING",(0,0),(-1,-1),2.5)]))
    return t

def _placeholder(headers, message, widths, main):
    hs = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=5.2, leading=6, textColor=colors.white, alignment=TA_CENTER)
    data = [[Paragraph(escape(h), hs) for h in headers], [message] + [""]*(len(headers)-1)]
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),main),("TEXTCOLOR",(0,0),(-1,0),colors.white),("ALIGN",(0,0),(-1,0),"CENTER"),("SPAN",(0,1),(-1,1)),("ALIGN",(0,1),(-1,1),"CENTER"),("TEXTCOLOR",(0,1),(-1,1),MUTED),("FONTSIZE",(0,1),(-1,1),6.5),("GRID",(0,0),(-1,-1),.35,GRID),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    return t

def _photo(person, width, height, soft, ink):
    result = get_drive_photo_data_url(person.get("drive_file_id"), cache_key=str(person.get("badge_number") or "photo"))
    if result.get("ok") and result.get("data_url"):
        try:
            img = Image(BytesIO(base64.b64decode(result["data_url"].split(",",1)[1])), width=width, height=height); img.hAlign="CENTER"; return img
        except Exception: pass
    initials = "".join(str(person.get(k) or "?").strip()[:1] for k in ("first_name","last_name")).upper()
    t = Table([[initials]], colWidths=[width], rowHeights=[height])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),soft),("BOX",(0,0),(-1,-1),.8,ink),("TEXTCOLOR",(0,0),(-1,-1),ink),("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),25),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    return t

def generate_profile_pdf(person: dict[str, Any], output_path: Path | str) -> Path:
    output_path = Path(output_path); output_path.parent.mkdir(parents=True, exist_ok=True)
    main, ink, soft = _theme(person)
    page_width, left_width, gap = 186*mm, 49*mm, 5*mm
    right_width = page_width-left_width-gap
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=12*mm, leftMargin=12*mm, topMargin=8*mm, bottomMargin=8*mm, title=f"Personnel Profile - {_full_name(person)}", author="NBP Personnel Lookup")
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=19, leading=21, textColor=ink, alignment=TA_CENTER)
    sub = ParagraphStyle("sub", fontName="Helvetica", fontSize=7, leading=8, textColor=ink, alignment=TA_CENTER)
    name = ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=10.5, leading=12, textColor=ink, alignment=TA_CENTER, wordWrap="CJK")
    rank = ParagraphStyle("rank", fontName="Helvetica-Bold", fontSize=7, leading=8, textColor=ink, alignment=TA_CENTER)
    story = [Paragraph("PERSONNEL PROFILE",title), Paragraph("PERSONNEL OFFICE & MOVEMENT TRACKING",sub), Spacer(1,2*mm)]
    rule=Table([[""]],colWidths=[page_width],rowHeights=[.7*mm]); rule.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),main)])); story += [rule,Spacer(1,3*mm)]

    identity_rows=[("Badge Number",person.get("badge_number")),("ID Number",person.get("id_number")),("Personnel Type",person.get("personnel_type")),("Gender",person.get("gender"))]
    personal_rows=[("Birthdate",_birthdate_text(person.get("birthdate"))),("Age",_age(person.get("birthdate"))),("Place of Birth",person.get("place_of_birth")),("Civil Status",person.get("civil_status")),("Citizenship",person.get("citizenship")),("Religion",person.get("religion")),("Blood Type",person.get("blood_type")),("Height",person.get("height")),("Weight",person.get("weight")),("Email",person.get("email")),("TIN",person.get("tin")),("Highest Education",person.get("highest_education")),("Home Address",_home_address(person))]
    parent_rows=[("Father's Name",person.get("father_name")),("Address",person.get("father_address")),("Mother's Name",person.get("mother_name")),("Address",person.get("mother_address"))]
    emergency_rows=[("Contact Person",person.get("emergency_contact")),("Relationship",person.get("emergency_relationship")),("Contact Number",person.get("emergency_number")),("Address",person.get("emergency_address"))]
    left=[_photo(person,43*mm,48*mm,soft,ink),Spacer(1,1.5*mm),Paragraph(escape(_full_name(person).upper()),name),Paragraph(escape(_value(person.get("rank"))),rank),Spacer(1,1.5*mm),_info_table(identity_rows,left_width-2*mm,soft)]
    for heading, rows in [("PERSONAL INFORMATION",personal_rows),("PARENTS",parent_rows),("EMERGENCY CONTACT",emergency_rows)]:
        left += [Spacer(1,1.6*mm),_section_title(heading,left_width-2*mm,main),_info_table(rows,left_width-2*mm,soft)]

    current_rows=[("Office",person.get("office")),("Camp",person.get("camp")),("Rank",person.get("rank")),("Classification",person.get("classification")),("Personnel Status",person.get("personnel_status"))]
    right=[_section_title("CURRENT OFFICE INFORMATION",right_width,main),_info_table(current_rows,right_width,soft,30*mm),Spacer(1,3*mm),_section_title("OFFICE MOVEMENT HISTORY",right_width,main),_placeholder(["#","From Office","To Office","Position","From Date","To Date","Remarks"],"No office movement records yet.",[6*mm,22*mm,22*mm,22*mm,16*mm,16*mm,right_width-104*mm],main),Spacer(1,3*mm),_section_title("MEMO",right_width,main),_placeholder(["Doc No.","Title","Type","Date"],"No memo records yet.",[25*mm,55*mm,25*mm,right_width-105*mm],main),Spacer(1,3*mm),_section_title("COMMENDATIONS / RECOGNITIONS",right_width,main),_placeholder(["Date Received","Award / Title","Presented By","Remarks"],"No commendation records yet.",[24*mm,40*mm,32*mm,right_width-96*mm],main)]

    top=Table([[left,"",right]],colWidths=[left_width,gap,right_width],hAlign="LEFT")
    top.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0),("LINEAFTER",(0,0),(0,0),.45,GRID)]))
    story += [top,Spacer(1,2.5*mm)]
    generated=datetime.now().strftime("%B %d, %Y %I:%M %p")
    footer=Table([["PREPARED BY: ____________________",f"DATE GENERATED: {generated}"]],colWidths=[93*mm,93*mm])
    footer.setStyle(TableStyle([("LINEABOVE",(0,0),(-1,0),.4,GRID),("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),6.2),("TEXTCOLOR",(0,0),(-1,-1),ink),("ALIGN",(1,0),(1,0),"RIGHT"),("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(KeepTogether(footer)); doc.build(story); return output_path
