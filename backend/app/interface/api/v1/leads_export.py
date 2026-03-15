from __future__ import annotations

import csv
import zipfile
from io import BytesIO, StringIO
from xml.etree import ElementTree as ET

from app.application.dtos import LeadExportRow


EXPORT_COLUMNS: tuple[str, ...] = (
    "lead_uid",
    "title",
    "notes",
    "owner",
    "stage",
    "entered_at",
    "source_code",
)


def render_leads_csv(rows: list[LeadExportRow]) -> bytes:
    stream = StringIO()
    writer = csv.writer(stream, delimiter=";", lineterminator="\n")
    writer.writerow(EXPORT_COLUMNS)
    for row in rows:
        writer.writerow(_row_to_values(row))
    return stream.getvalue().encode("utf-8-sig")


def render_leads_xlsx(rows: list[LeadExportRow]) -> bytes:
    table = [list(EXPORT_COLUMNS)] + [_row_to_values(row) for row in rows]

    xlsx = BytesIO()
    with zipfile.ZipFile(xlsx, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _content_types_xml())
        zf.writestr("_rels/.rels", _root_rels_xml())
        zf.writestr("xl/workbook.xml", _workbook_xml())
        zf.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml())
        zf.writestr("xl/styles.xml", _styles_xml())
        zf.writestr("xl/worksheets/sheet1.xml", _sheet_xml(table))

    return xlsx.getvalue()


def _row_to_values(row: LeadExportRow) -> list[str]:
    entered_at = row.entered_at.isoformat() if row.entered_at is not None else ""
    return [
        row.lead_uid,
        row.title or "",
        row.notes or "",
        str(row.owner),
        str(row.stage),
        entered_at,
        str(row.source_code),
    ]


_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _sheet_xml(table: list[list[str]]) -> bytes:
    worksheet = ET.Element(f"{{{_NS_MAIN}}}worksheet")
    sheet_data = ET.SubElement(worksheet, f"{{{_NS_MAIN}}}sheetData")

    for r_idx, values in enumerate(table, start=1):
        row_el = ET.SubElement(sheet_data, f"{{{_NS_MAIN}}}row", {"r": str(r_idx)})
        for c_idx, value in enumerate(values, start=1):
            cell_ref = f"{_col_letter(c_idx)}{r_idx}"
            c = ET.SubElement(
                row_el,
                f"{{{_NS_MAIN}}}c",
                {"r": cell_ref, "t": "inlineStr"},
            )
            is_el = ET.SubElement(c, f"{{{_NS_MAIN}}}is")
            t_el = ET.SubElement(is_el, f"{{{_NS_MAIN}}}t")
            t_el.text = value

    return ET.tostring(worksheet, encoding="utf-8", xml_declaration=True)


def _col_letter(index: int) -> str:
    # 1-based index
    result = ""
    n = index
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(ord("A") + rem) + result
    return result


def _workbook_xml() -> bytes:
    workbook = ET.Element(
        f"{{{_NS_MAIN}}}workbook",
        {"xmlns:r": _NS_RELS},
    )
    sheets = ET.SubElement(workbook, f"{{{_NS_MAIN}}}sheets")
    ET.SubElement(
        sheets,
        f"{{{_NS_MAIN}}}sheet",
        {"name": "Leads", "sheetId": "1", f"{{{_NS_RELS}}}id": "rId1"},
    )
    return ET.tostring(workbook, encoding="utf-8", xml_declaration=True)


def _workbook_rels_xml() -> bytes:
    rels = ET.Element(
        "Relationships",
        {"xmlns": "http://schemas.openxmlformats.org/package/2006/relationships"},
    )
    ET.SubElement(
        rels,
        "Relationship",
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
            "Target": "worksheets/sheet1.xml",
        },
    )
    ET.SubElement(
        rels,
        "Relationship",
        {
            "Id": "rId2",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
            "Target": "styles.xml",
        },
    )
    return ET.tostring(rels, encoding="utf-8", xml_declaration=True)


def _root_rels_xml() -> bytes:
    rels = ET.Element(
        "Relationships",
        {"xmlns": "http://schemas.openxmlformats.org/package/2006/relationships"},
    )
    ET.SubElement(
        rels,
        "Relationship",
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "Target": "xl/workbook.xml",
        },
    )
    return ET.tostring(rels, encoding="utf-8", xml_declaration=True)


def _content_types_xml() -> bytes:
    types = ET.Element(
        "Types",
        {"xmlns": "http://schemas.openxmlformats.org/package/2006/content-types"},
    )
    ET.SubElement(types, "Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    ET.SubElement(types, "Default", {"Extension": "xml", "ContentType": "application/xml"})
    ET.SubElement(
        types,
        "Override",
        {
            "PartName": "/xl/workbook.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
        },
    )
    ET.SubElement(
        types,
        "Override",
        {
            "PartName": "/xl/worksheets/sheet1.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
        },
    )
    ET.SubElement(
        types,
        "Override",
        {
            "PartName": "/xl/styles.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml",
        },
    )
    return ET.tostring(types, encoding="utf-8", xml_declaration=True)


def _styles_xml() -> bytes:
    style_sheet = ET.Element(f"{{{_NS_MAIN}}}styleSheet")

    fonts = ET.SubElement(style_sheet, f"{{{_NS_MAIN}}}fonts", {"count": "1"})
    font = ET.SubElement(fonts, f"{{{_NS_MAIN}}}font")
    ET.SubElement(font, f"{{{_NS_MAIN}}}sz", {"val": "11"})
    ET.SubElement(font, f"{{{_NS_MAIN}}}color", {"theme": "1"})
    ET.SubElement(font, f"{{{_NS_MAIN}}}name", {"val": "Calibri"})
    ET.SubElement(font, f"{{{_NS_MAIN}}}family", {"val": "2"})

    fills = ET.SubElement(style_sheet, f"{{{_NS_MAIN}}}fills", {"count": "2"})
    ET.SubElement(ET.SubElement(fills, f"{{{_NS_MAIN}}}fill"), f"{{{_NS_MAIN}}}patternFill", {"patternType": "none"})
    ET.SubElement(ET.SubElement(fills, f"{{{_NS_MAIN}}}fill"), f"{{{_NS_MAIN}}}patternFill", {"patternType": "gray125"})

    borders = ET.SubElement(style_sheet, f"{{{_NS_MAIN}}}borders", {"count": "1"})
    border = ET.SubElement(borders, f"{{{_NS_MAIN}}}border")
    ET.SubElement(border, f"{{{_NS_MAIN}}}left")
    ET.SubElement(border, f"{{{_NS_MAIN}}}right")
    ET.SubElement(border, f"{{{_NS_MAIN}}}top")
    ET.SubElement(border, f"{{{_NS_MAIN}}}bottom")
    ET.SubElement(border, f"{{{_NS_MAIN}}}diagonal")

    cell_style_xfs = ET.SubElement(style_sheet, f"{{{_NS_MAIN}}}cellStyleXfs", {"count": "1"})
    ET.SubElement(cell_style_xfs, f"{{{_NS_MAIN}}}xf", {"numFmtId": "0", "fontId": "0", "fillId": "0", "borderId": "0"})

    cell_xfs = ET.SubElement(style_sheet, f"{{{_NS_MAIN}}}cellXfs", {"count": "1"})
    ET.SubElement(
        cell_xfs,
        f"{{{_NS_MAIN}}}xf",
        {"numFmtId": "0", "fontId": "0", "fillId": "0", "borderId": "0", "xfId": "0"},
    )

    cell_styles = ET.SubElement(style_sheet, f"{{{_NS_MAIN}}}cellStyles", {"count": "1"})
    ET.SubElement(cell_styles, f"{{{_NS_MAIN}}}cellStyle", {"name": "Normal", "xfId": "0", "builtinId": "0"})

    return ET.tostring(style_sheet, encoding="utf-8", xml_declaration=True)
