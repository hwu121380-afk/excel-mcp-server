"""Tests for workbook inspect / clean / convert."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from excel_mcp_server.workbook import (
    clean_workbook,
    csv_to_xlsx,
    inspect_workbook,
    xlsx_to_csv,
)


def _make_xlsx(path: Path, rows) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"
    for row in rows:
        ws.append(row)
    wb.save(path)
    return path


def test_inspect_reports_headers_counts_and_preview(tmp_path):
    path = _make_xlsx(
        tmp_path / "orders.xlsx",
        [["order_id", "product"], ["1", "pen"], ["2", "book"], ["3", "ruler"]],
    )
    result = inspect_workbook(path)
    sheet = result["sheets"][0]
    assert sheet["name"] == "Orders"
    assert sheet["headers"] == ["order_id", "product"]
    assert sheet["data_rows"] == 3
    assert sheet["preview"][0] == ["1", "pen"]


def test_clean_trims_dedupes_and_drops_blanks(tmp_path):
    src = _make_xlsx(
        tmp_path / "messy.xlsx",
        [
            ["  order_id ", "product"],
            ["1", "  pen "],
            ["1", "pen"],
            ["", ""],
            ["2", "book"],
        ],
    )
    dst = tmp_path / "clean.xlsx"
    result = clean_workbook(src, dst)
    sheet = result["sheets"][0]
    assert sheet["rows_in"] == 4
    assert sheet["rows_out"] == 2
    assert sheet["duplicates_removed"] == 1
    assert sheet["blank_rows_removed"] == 1
    wb = load_workbook(dst)
    ws = wb["Orders"]
    assert [c.value for c in ws[1]] == ["order_id", "product"]
    assert [c.value for c in ws[2]] == ["1", "pen"]
    # the input file is untouched
    assert [c.value for c in load_workbook(src)["Orders"][1]] == ["  order_id ", "product"]


def test_clean_refuses_to_overwrite_input(tmp_path):
    src = _make_xlsx(tmp_path / "a.xlsx", [["x"], ["1"]])
    with pytest.raises(ValueError):
        clean_workbook(src, src)


def test_csv_xlsx_roundtrip(tmp_path):
    csv_path = tmp_path / "in.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "product"])
        writer.writerow(["1", "pen"])
    xlsx_path = tmp_path / "out.xlsx"
    converted = csv_to_xlsx(csv_path, xlsx_path)
    assert converted["rows"] == 2
    back = tmp_path / "back.csv"
    result = xlsx_to_csv(xlsx_path, back)
    assert result["rows"] == 2
    with open(back, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows == [["order_id", "product"], ["1", "pen"]]
