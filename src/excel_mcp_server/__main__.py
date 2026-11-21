"""Console entry point: `excel-mcp-server` starts the MCP server (stdio)."""

from __future__ import annotations

from .server import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()
