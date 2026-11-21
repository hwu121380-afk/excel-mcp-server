"""Read, clean and convert .xlsx workbooks (openpyxl).

Every function takes explicit file paths. Cleaning and conversion always
write a *new* file and refuse to overwrite their input, so an agent can
never destroy the original by mistake.
"""

from __future__ import annotations

import csv
import datetime as _dt
from pathlib import Path

from openpyxl import Workbook, load_workbook

MAX_PREVIEW_ROWS = 5


def _jsonable(value):
    """Make an openpyxl cell value safe for JSON (MCP responses)."""
    if isinstance(value, (_dt.datetime, _dt.date)):
        return value.isoformat()
    if isinstance(value, (_dt.time, _dt.timedelta)):
        return str(value)
    return value


def _is_blank_row(row) -> bool:
    return all(v is None or (isinstance(v, str) and v.strip() == "") for v in row)


def _clean_header(value):
    if isinstance(value, str):
        return " ".join(value.split())
    return value


def _clean_value(value):
    if isinstance(value, str):
        return value.strip()
    return value


def _check_paths(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise FileNotFoundError(f"no such file: {src}")
    if src.resolve() == dst.resolve():
        raise ValueError("output_path must be a different file from the input")


def inspect_workbook(path) -> dict:
    """Return each sheet's headers, data-row count and a small preview.

    Read-only. Call this before cleaning or converting so you know what is
    inside the workbook.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"no such file: {path}")
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        sheets = []
        for ws in wb.worksheets:
            rows = ws.iter_rows(values_only=True)
            header = next(rows, None)
            preview: list[list] = []
            data_rows = 0
            for row in rows:
                if _is_blank_row(row):
                    continue
                data_rows += 1
                if len(preview) < MAX_PREVIEW_ROWS:
                    preview.append([_jsonable(v) for v in row])
            sheets.append(
                {
                    "name": ws.title,
                    "headers": [_jsonable(v) for v in header] if header else [],
                    "data_rows": data_rows,
                    "preview": preview,
                }
            )
    finally:
        wb.close()
    return {"path": str(path), "sheets": sheets}


def clean_workbook(input_path, output_path) -> dict:
    """Write a cleaned copy of a workbook.

    - header cells: whitespace collapsed ("  Product  Name " -> "Product Name")
    - string cells: leading/trailing whitespace stripped
    - fully blank rows: dropped
    - exact-duplicate data rows: dropped, first copy kept

    The input file is never modified. Cell formatting is not preserved.
    """
    src = Path(input_path)
    dst = Path(output_path)
    _check_paths(src, dst)
    wb = load_workbook(src)
    report: dict = {"input": str(src), "output": str(dst), "sheets": []}
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            report["sheets"].append(
                {
                    "name": ws.title,
                    "rows_in": 0,
                    "rows_out": 0,
                    "duplicates_removed": 0,
                    "blank_rows_removed": 0,
                }
            )
            continue
        header = [_clean_header(v) for v in rows[0]]
        seen: set[tuple] = set()
        kept: list[list] = [header]
        rows_in = len(rows) - 1
        duplicates = 0
        blanks = 0
        for row in rows[1:]:
            if _is_blank_row(row):
                blanks += 1
                continue
            cleaned = [_clean_value(v) for v in row]
            key = tuple(cleaned)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            kept.append(cleaned)
        ws.delete_rows(1, ws.max_row)
        for row in kept:
            ws.append(row)
        report["sheets"].append(
            {
                "name": ws.title,
                "rows_in": rows_in,
                "rows_out": len(kept) - 1,
                "duplicates_removed": duplicates,
                "blank_rows_removed": blanks,
            }
        )
    dst.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dst)
    return report


def csv_to_xlsx(input_path, output_path, sheet_name: str = "Sheet1") -> dict:
    """Convert a .csv file to .xlsx (one sheet)."""
    src = Path(input_path)
    dst = Path(output_path)
    _check_paths(src, dst)
    with open(src, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    for row in rows:
        ws.append(row)
    dst.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dst)
    return {
        "input": str(src),
        "output": str(dst),
        "rows": len(rows),
        "columns": len(rows[0]) if rows else 0,
    }


def xlsx_to_csv(input_path, output_path, sheet: str | None = None) -> dict:
    """Convert one sheet of an .xlsx file to .csv (defaults to first sheet)."""
    src = Path(input_path)
    dst = Path(output_path)
    _check_paths(src, dst)
    wb = load_workbook(src, read_only=True, data_only=True)
    try:
        ws = wb[sheet] if sheet else wb.worksheets[0]
        title = ws.title
        rows = list(ws.iter_rows(values_only=True))
    finally:
        wb.close()
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(
                [
                    "" if v is None else v.isoformat()
                    if isinstance(v, (_dt.datetime, _dt.date))
                    else v
                    for v in row
                ]
            )
    return {"input": str(src), "output": str(dst), "sheet": title, "rows": len(rows)}
