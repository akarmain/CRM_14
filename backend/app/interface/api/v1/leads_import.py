from __future__ import annotations

import csv
import re
import zipfile
from dataclasses import dataclass
from io import BytesIO, StringIO
from typing import Any
from xml.etree import ElementTree as ET

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.domain.enums import SourcesCode, Users


class LeadImportRow(BaseModel):
    owner: Users
    title: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    source_code: SourcesCode
    lead_uid: str | None = Field(default=None, max_length=32)

    @field_validator("lead_uid", mode="before")
    @classmethod
    def _normalize_lead_uid(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        return value


@dataclass(frozen=True, slots=True)
class LeadImportRowError:
    row: int
    message: str


class LeadsImportError(Exception):
    def __init__(self, message: str, *, errors: list[LeadImportRowError] | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []

    def as_detail(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "errors": [{"row": e.row, "message": e.message} for e in self.errors],
        }


_REQUIRED_COLUMNS = ("owner", "title", "notes", "source_code")
_OPTIONAL_COLUMNS = ("lead_uid",)


def parse_leads_import(
    data: bytes,
    *,
    filename: str | None = None,
    content_type: str | None = None,
    default_owner: Users | None = None,
) -> list[LeadImportRow]:
    fmt = _detect_format(filename=filename, content_type=content_type)

    if fmt == "csv":
        return _parse_csv(data, default_owner=default_owner)
    if fmt == "xlsx":
        return _parse_xlsx(data, default_owner=default_owner)

    errors: list[str] = []
    for fallback in ("csv", "xlsx"):
        try:
            if fallback == "csv":
                return _parse_csv(data, default_owner=default_owner)
            return _parse_xlsx(data, default_owner=default_owner)
        except LeadsImportError as exc:
            errors.append(f"{fallback}: {exc.message}")

    raise LeadsImportError(
        "Unsupported file format. Provide .csv (recommended) or .xlsx, "
        "or set Content-Type accordingly.",
        errors=[LeadImportRowError(row=0, message="; ".join(errors))] if errors else None,
    )


def _detect_format(*, filename: str | None, content_type: str | None) -> str | None:
    if filename:
        lowered = filename.lower().strip()
        if lowered.endswith(".csv"):
            return "csv"
        if lowered.endswith(".xlsx"):
            return "xlsx"

    if content_type:
        ct = content_type.lower()
        if "text/csv" in ct or ct.endswith("/csv"):
            return "csv"
        if "spreadsheetml" in ct or "application/vnd.ms-excel" in ct:
            return "xlsx"

    return None


def _parse_csv(data: bytes, *, default_owner: Users | None) -> list[LeadImportRow]:
    text = _decode_text(data)
    # Normalize newlines and allow both ',' and ';' delimiters.
    stream = StringIO(text.replace("\r\n", "\n").replace("\r", "\n"))
    sample = stream.read(4096)
    stream.seek(0)
    delimiter = ";"
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        delimiter = dialect.delimiter
    except csv.Error:
        pass

    reader = csv.DictReader(stream, delimiter=delimiter)
    if reader.fieldnames is None:
        raise LeadsImportError("CSV header row is missing.")

    header_map = _build_header_map(reader.fieldnames, default_owner=default_owner)
    rows: list[LeadImportRow] = []
    errors: list[LeadImportRowError] = []

    for idx, raw in enumerate(reader, start=2):
        if _row_is_empty(raw):
            continue
        payload = _extract_row_payload(raw, header_map, row_number=idx, default_owner=default_owner)
        try:
            rows.append(LeadImportRow.model_validate(payload))
        except ValidationError as exc:
            errors.append(LeadImportRowError(row=idx, message=_format_validation_error(exc)))

    if errors:
        raise LeadsImportError("Some rows are invalid.", errors=errors)
    if not rows:
        raise LeadsImportError("No leads found in the file.")
    return rows


def _parse_xlsx(data: bytes, *, default_owner: Users | None) -> list[LeadImportRow]:
    try:
        zf = zipfile.ZipFile(BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise LeadsImportError("XLSX file is not a valid zip archive.") from exc

    sheet_path = _xlsx_first_sheet_path(zf)
    shared_strings = _xlsx_shared_strings(zf)
    rows = _xlsx_read_rows(zf, sheet_path, shared_strings)
    if not rows:
        raise LeadsImportError("XLSX contains no rows.")

    header = [str(v or "").strip() for v in rows[0]]
    header_map = _build_header_map(header, default_owner=default_owner)

    out: list[LeadImportRow] = []
    errors: list[LeadImportRowError] = []
    for i, values in enumerate(rows[1:], start=2):
        raw_dict = {header[j]: (values[j] if j < len(values) else None) for j in range(len(header))}
        if _row_is_empty(raw_dict):
            continue
        payload = _extract_row_payload(
            raw_dict,
            header_map,
            row_number=i,
            default_owner=default_owner,
        )
        try:
            out.append(LeadImportRow.model_validate(payload))
        except ValidationError as exc:
            errors.append(LeadImportRowError(row=i, message=_format_validation_error(exc)))

    if errors:
        raise LeadsImportError("Some rows are invalid.", errors=errors)
    if not out:
        raise LeadsImportError("No leads found in the file.")
    return out


def _decode_text(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise LeadsImportError("Unable to decode CSV file as UTF-8 or CP1251.")


def _normalize_column(name: str) -> str:
    return re.sub(r"[\s\-]+", "_", name.strip().lower())


def _build_header_map(fieldnames: list[str], *, default_owner: Users | None) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for name in fieldnames:
        normalized = _normalize_column(name)
        if normalized:
            mapping[normalized] = name

    required_columns = tuple(
        col for col in _REQUIRED_COLUMNS if not (col == "owner" and default_owner is not None)
    )
    missing = [col for col in required_columns if col not in mapping]
    if missing:
        raise LeadsImportError(f"Missing required columns: {', '.join(missing)}.")
    return mapping


def _row_is_empty(row: dict[str, Any]) -> bool:
    for v in row.values():
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        return False
    return True


def _extract_row_payload(
    raw_row: dict[str, Any],
    header_map: dict[str, str],
    *,
    row_number: int,
    default_owner: Users | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for required in _REQUIRED_COLUMNS:
        if required == "owner" and default_owner is not None and required not in header_map:
            out[required] = default_owner
            continue

        key = header_map[required]
        out[required] = _normalize_cell_value(raw_row.get(key))

    for optional in _OPTIONAL_COLUMNS:
        key = header_map.get(optional)
        if key is not None:
            out[optional] = _normalize_cell_value(raw_row.get(key))

    if out["owner"] is None:
        raise LeadsImportError("Some rows are invalid.", errors=[LeadImportRowError(row=row_number, message="owner is required")])
    if out["source_code"] is None:
        raise LeadsImportError(
            "Some rows are invalid.",
            errors=[LeadImportRowError(row=row_number, message="source_code is required")],
        )
    return out


def _normalize_cell_value(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    return value


def _format_validation_error(exc: ValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        if loc:
            parts.append(f"{loc}: {msg}")
        else:
            parts.append(str(msg))
    return "; ".join(parts) if parts else "Invalid value"


def _xlsx_first_sheet_path(zf: zipfile.ZipFile) -> str:
    # Best-effort: resolve the first worksheet via workbook relationships.
    try:
        wb_xml = zf.read("xl/workbook.xml")
    except KeyError:
        if "xl/worksheets/sheet1.xml" in zf.namelist():
            return "xl/worksheets/sheet1.xml"
        raise LeadsImportError("XLSX is missing xl/workbook.xml.")

    rels: dict[str, str] = {}
    try:
        rels_xml = zf.read("xl/_rels/workbook.xml.rels")
        rels_root = ET.fromstring(rels_xml)
        for rel in rels_root.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
            r_id = rel.attrib.get("Id")
            target = rel.attrib.get("Target")
            if r_id and target and "worksheets/" in target:
                rels[r_id] = f"xl/{target.lstrip('/')}"
    except KeyError:
        rels = {}

    root = ET.fromstring(wb_xml)
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    sheet = root.find(".//m:sheets/m:sheet", ns)
    if sheet is None:
        raise LeadsImportError("XLSX workbook has no sheets.")

    r_id = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    if r_id and r_id in rels and rels[r_id] in zf.namelist():
        return rels[r_id]

    if "xl/worksheets/sheet1.xml" in zf.namelist():
        return "xl/worksheets/sheet1.xml"
    raise LeadsImportError("Unable to locate the first worksheet inside XLSX.")


def _xlsx_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    try:
        xml = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []

    root = ET.fromstring(xml)
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    out: list[str] = []
    for si in root.findall(".//m:si", ns):
        texts = [t.text or "" for t in si.findall(".//m:t", ns)]
        out.append("".join(texts))
    return out


def _xlsx_cell_value(cell: ET.Element, shared_strings: list[str]) -> str | None:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    cell_type = cell.attrib.get("t")
    value_el = cell.find("m:v", ns)
    if cell_type == "s":
        if value_el is None or value_el.text is None:
            return None
        try:
            idx = int(value_el.text)
            return shared_strings[idx] if 0 <= idx < len(shared_strings) else None
        except ValueError:
            return None
    if cell_type == "inlineStr":
        t_el = cell.find(".//m:t", ns)
        return (t_el.text or "") if t_el is not None else None
    if value_el is None or value_el.text is None:
        return None
    return value_el.text


def _xlsx_col_index(cell_ref: str) -> int:
    # "AB12" -> 28 (1-based); returns 0 for invalid refs.
    m = re.match(r"^([A-Za-z]+)", cell_ref)
    if not m:
        return 0
    letters = m.group(1).upper()
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx


def _xlsx_read_rows(
    zf: zipfile.ZipFile,
    sheet_path: str,
    shared_strings: list[str],
) -> list[list[str | None]]:
    try:
        xml = zf.read(sheet_path)
    except KeyError as exc:
        raise LeadsImportError(f"Worksheet '{sheet_path}' not found.") from exc

    root = ET.fromstring(xml)
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    out: list[list[str | None]] = []

    for row in root.findall(".//m:sheetData/m:row", ns):
        cells = row.findall("m:c", ns)
        values_by_col: dict[int, str | None] = {}
        max_col = 0
        for cell in cells:
            ref = cell.attrib.get("r", "")
            col = _xlsx_col_index(ref)
            if col <= 0:
                continue
            max_col = max(max_col, col)
            values_by_col[col] = _xlsx_cell_value(cell, shared_strings)

        if max_col == 0:
            out.append([])
            continue

        # 1-based to 0-based list
        out.append([values_by_col.get(i) for i in range(1, max_col + 1)])

    return out
