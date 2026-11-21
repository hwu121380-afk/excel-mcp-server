# excel-mcp-server

[![CI](https://github.com/hwu121380-afk/excel-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/hwu121380-afk/excel-mcp-server/actions/workflows/ci.yml)

An MCP server that lets an AI coding agent work with Excel and CSV files:
inspect a workbook, merge a folder of CSVs, clean a messy workbook, and
convert between `.csv` and `.xlsx`.

It speaks the [Model Context Protocol](https://modelcontextprotocol.io/) over
stdio, so it plugs straight into Claude Code, Cursor, Claude Desktop and any
other MCP client. The merge check is borrowed from
[csv-merge-check](https://github.com/hwu121380-afk/csv-merge-check): rows in
must equal rows out.

## Tools

| Tool | What it does |
| --- | --- |
| `inspect_workbook` | Sheets, headers, data-row counts and the first rows. Read-only. |
| `merge_csv_files` | Merge every `.csv` in a folder into one CSV, with a row-count check. |
| `clean_workbook` | Write a cleaned copy: trim whitespace, collapse header whitespace, drop blank rows and exact-duplicate rows. |
| `csv_to_xlsx` | Convert a `.csv` file to `.xlsx`. |
| `xlsx_to_csv` | Convert one sheet of an `.xlsx` file to `.csv`. |

## What it does not do

- It never overwrites its input. Cleaning, merging and conversion always
  write a new file and refuse when the output path is the input file.
- It does not preserve cell formatting when cleaning. The cleaned workbook
  keeps values, not styles.
- It does not guess missing values, repair dates or parse currency amounts.
- It does not read anything except the file paths the caller passes, and it
  makes no network requests.

## What you need

- Python 3.10 or newer
- `pip install excel-mcp-server` (or clone this repo and `pip install -e .`)

## 1. Install

```bash
pip install excel-mcp-server
```

Or from source:

```bash
git clone https://github.com/hwu121380-afk/excel-mcp-server.git
cd excel-mcp-server
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## 2. Connect it to your agent

Claude Code:

```bash
claude mcp add excel-mcp-server -- excel-mcp-server
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "excel-mcp-server": {
      "command": "excel-mcp-server"
    }
  }
}
```

If you installed from source, use the full path to the virtual environment's
binary instead of `excel-mcp-server`, for example
`/home/you/excel-mcp-server/.venv/bin/excel-mcp-server`.

## 3. Try it

Ask your agent something like:

> Inspect `sample_input/orders.xlsx`, then clean it into
> `sample_input/orders_clean.xlsx` and tell me how many duplicates it had.

Or try the merge check on the bundled samples:

> Merge the CSVs in `sample_input/` into `merged.csv` and check the row counts.

The files in `sample_input/` are **SAMPLE – FICTIONAL DATA**. They are not
from a real shop or a real customer.

## Development

```bash
pip install -e ".[dev]"
python -m pytest -q
```

## 中文简介

这是一个 MCP 服务器，让 AI 编程助手能直接操作 Excel 和 CSV 文件：查看表
格结构、合并一文件夹的 CSV、清洗脏数据（去重、去空格、去空行）、CSV 和
xlsx 互转。清洗与合并永远写新文件，绝不覆盖原文件，适合接单时处理客户
发来的表格，也适合放进简历。

## License

MIT. See [LICENSE](LICENSE).
