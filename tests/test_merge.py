"""Tests for the CSV merge + row-count check."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from excel_mcp_server.merge import merge_csv_files


def _write_csv(path: Path, header, rows) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def test_merge_keeps_union_of_columns(tmp_path):
    _write_csv(tmp_path / "a.csv", ["order_id", "product"], [["1", "pen"], ["2", "book"]])
    _write_csv(tmp_path / "b.csv", ["order_id", "qty"], [["3", "5"], ["4", "2"]])
    out = tmp_path / "merged.csv"
    result = merge_csv_files(tmp_path, out)
    assert result["columns"] == ["order_id", "product", "qty"]
    assert result["rows_in"] == 4
    assert result["rows_out"] == 4
    assert result["ok"] is True
    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0] == {"order_id": "1", "product": "pen", "qty": ""}
    assert rows[2] == {"order_id": "3", "product": "", "qty": "5"}


def test_merge_counts_exact_duplicates_without_removing(tmp_path):
    _write_csv(tmp_path / "a.csv", ["order_id", "product"], [["1", "pen"]])
    _write_csv(tmp_path / "b.csv", ["order_id", "product"], [["1", "pen"]])
    result = merge_csv_files(tmp_path, tmp_path / "merged.csv")
    assert result["rows_in"] == 2
    assert result["rows_out"] == 2
    assert result["exact_duplicates"] == 1
    assert result["ok"] is True


def test_merge_skips_blank_rows(tmp_path):
    _write_csv(
        tmp_path / "a.csv",
        ["order_id", "product"],
        [["1", "pen"], ["", ""], ["2", "book"]],
    )
    result = merge_csv_files(tmp_path, tmp_path / "merged.csv")
    assert result["rows_in"] == 2
    assert result["rows_out"] == 2
    assert result["ok"] is True


def test_merge_refuses_output_inside_input_folder(tmp_path):
    _write_csv(tmp_path / "a.csv", ["x"], [["1"]])
    with pytest.raises(ValueError):
        merge_csv_files(tmp_path, tmp_path / "a.csv")


def test_merge_empty_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        merge_csv_files(tmp_path, tmp_path / "merged.csv")
