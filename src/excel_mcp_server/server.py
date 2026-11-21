"""MCP server: Excel and CSV tools for AI coding agents.

Run with:  excel-mcp-server        (stdio transport)
or:        python -m excel_mcp_server

Tools only touch the file paths the caller passes. Cleaning and merging
always write a new file and refuse to overwrite their input.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .merge import merge_csv_files as _merge_csv_files
from .workbook import (
    clean_workbook as _clean_workbook,
    csv_to_xlsx as _csv_to_xlsx,
    inspect_workbook as _inspect_workbook,
    xlsx_to_csv as _xlsx_to_csv,
)

mcp = FastMCP("excel-mcp-server")


@mcp.tool()
def inspect_workbook(path: str) -> dict:
    """Inspect an .xlsx file: sheets, headers, data-row counts, first rows.

    Read-only. Use it before cleaning or converting so you know what is
    inside the workbook.
    """
    return _inspect_workbook(path)


@mcp.tool()
def merge_csv_files(input_dir: str, output_path: str) -> dict:
    """Merge every .csv file in a folder into one CSV, with a row-count check.

    Stacks data rows in file-name order and keeps the union of all columns.
    Fully blank rows are skipped. Exact-duplicate rows are counted, not
    removed. Returns per-file counts and ok=true when rows in == rows out.
    """
    return _merge_csv_files(input_dir, output_path)


@mcp.tool()
def clean_workbook(input_path: str, output_path: str) -> dict:
    """Write a cleaned copy of an .xlsx workbook.

    Trims whitespace, collapses header whitespace, drops fully blank rows
    and drops exact-duplicate data rows (first copy kept). The input file is
    never modified; output_path must be a different file. Cell formatting
    is not preserved.
    """
    return _clean_workbook(input_path, output_path)


@mcp.tool()
def csv_to_xlsx(input_path: str, output_path: str) -> dict:
    """Convert a .csv file to .xlsx (one sheet)."""
    return _csv_to_xlsx(input_path, output_path)


@mcp.tool()
def xlsx_to_csv(input_path: str, output_path: str, sheet: str | None = None) -> dict:
    """Convert one sheet of an .xlsx file to .csv. Defaults to the first sheet."""
    return _xlsx_to_csv(input_path, output_path, sheet)


def run() -> None:
    mcp.run()


if __name__ == "__main__":
    run()
