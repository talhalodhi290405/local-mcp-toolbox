"""MCP server exposing the Local MCP Toolbox tools over stdio."""

from __future__ import annotations

import json

from mcp.server import MCPServer

from local_mcp_toolbox.calculator import evaluate_expression
from local_mcp_toolbox.notes import search_notes as search_local_notes
from local_mcp_toolbox.system_info import get_system_info as read_system_info

mcp = MCPServer(
    "Local MCP Toolbox",
    instructions=(
        "A local MCP server with three tools: safe arithmetic evaluation, "
        "read-only search of configured Markdown/text notes, and non-sensitive "
        "platform information. Calculator expressions are never evaluated with eval()."
    ),
)


@mcp.tool()
def calculator(expression: str) -> str:
    """Safely evaluate a basic arithmetic expression and return JSON output.

    Supports numeric constants, parentheses, +, -, *, /, //, %, and **.
    Python code, names, function calls, and attribute access are not allowed.
    """

    return json.dumps(evaluate_expression(expression), ensure_ascii=False)


@mcp.tool()
def search_notes(query: str, limit: int = 5) -> str:
    """Search local .md and .txt notes in the configured notes directory.

    Configure the directory with MCP_TOOLBOX_NOTES_DIR. The caller supplies
    search terms, not a filesystem path. Returns ranked source snippets as JSON.
    """

    return json.dumps(search_local_notes(query, limit), ensure_ascii=False)


@mcp.tool()
def get_system_info() -> str:
    """Return basic OS, architecture, Python version, and CPU-count details.

    Usernames, hostnames, environment variables, network details, and process
    lists are intentionally excluded.
    """

    return json.dumps(read_system_info(), ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
