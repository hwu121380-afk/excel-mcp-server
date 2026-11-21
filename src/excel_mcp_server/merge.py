"""Merge every .csv file in a folder into one CSV, with a row-count check.

The idea comes from hwu121380-afk/csv-merge-check: stack the data rows in
file-name order, keep the union of all columns, skip fully blank rows, and
verify rows in == rows out. Exact-duplicate rows are counted, not removed.
"""

from __future__ import annotations

import csv
from pathlib import Path


def merge_csv_files(input_dir, output_path) -> dict:
    """Merge all top-level .csv files in `input_dir` into one CSV file."""
    src_dir = Path(input_dir)
    dst = Path(output_path)
    if not src_dir.is_dir():
        raise NotADirectoryError(f"no such folder: {src_dir}")
    files = sorted(
        p for p in src_dir.iterdir() if p.is_file() and p.suffix.lower() == ".csv"
    )
    if not files:
        raise FileNotFoundError(f"no .csv files in {src_dir}")
    if dst.resolve() in {p.resolve() for p in files}:
        raise ValueError("output_path must not be one of the input files")

    columns: list[str] = []
    seen_cols: set[str] = set()
    per_file: list[dict] = []
    all_rows: list[dict] = []
    total_in = 0

    for path in files:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for col in reader.fieldnames or []:
                if col not in seen_cols:
                    seen_cols.add(col)
                    columns.append(col)
            rows_in = 0
            for row in reader:
                values = {
                    k: (v if v is not None else "")
                    for k, v in row.items()
                    if k is not None
                }
                if all(v.strip() == "" for v in values.values()):
                    continue
                rows_in += 1
                all_rows.append(values)
            per_file.append({"file": path.name, "rows_in": rows_in})
            total_in += rows_in

    seen_rows: set[tuple] = set()
    duplicates = 0
    for values in all_rows:
        key = tuple(values.get(c, "") for c in columns)
        if key in seen_rows:
            duplicates += 1
            continue
        seen_rows.add(key)

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for values in all_rows:
            writer.writerow({c: values.get(c, "") for c in columns})

    total_out = len(all_rows)
    return {
        "input_dir": str(src_dir),
        "output": str(dst),
        "files": per_file,
        "columns": columns,
        "rows_in": total_in,
        "rows_out": total_out,
        "exact_duplicates": duplicates,
        "ok": total_in == total_out,
    }
