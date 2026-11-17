# Local MCP Toolbox

A local **Model Context Protocol (MCP)** server built with the official MCP Python SDK. It exposes three practical tools to an MCP-compatible host: safe arithmetic, read-only search across local Markdown/text notes, and basic non-sensitive system information.

The server uses the standard **stdio transport**, making it suitable for local MCP clients that launch the server as a subprocess.

## Features

- **`calculator`** — evaluates basic arithmetic using a restricted Python Abstract Syntax Tree (AST) evaluator. It does not use `eval()` and rejects names, function calls, attribute access, and unsupported syntax.
- **`search_notes`** — searches configured local `.md` and `.txt` files, ranks matches by simple keyword frequency, and returns short source-aware snippets.
- **`get_system_info`** — returns operating system, OS release, machine architecture, Python version, and logical CPU count.
- Uses MCP tool decorators and typed function arguments to expose tool schemas.
- Keeps system information intentionally limited: usernames, hostnames, environment variables, IP addresses, and process lists are not returned.
- Returns JSON-serialized tool results for straightforward inspection.

## Requirements

- Python 3.11 or newer
- pip
- An MCP-compatible host for interactive tool calls (for example, Claude Desktop)
- Optional: Node.js/npm/npx if you want to use the MCP Inspector

This project uses the official MCP Python SDK v2. See the [official SDK documentation](https://py.sdk.modelcontextprotocol.io/) for current SDK guidance.

## Installation

Clone the repository:

```bash
git clone https://github.com/talhalodhi290405/local-mcp-toolbox.git
cd local-mcp-toolbox
```

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project and its development dependency:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The `mcp[cli]` dependency installs the MCP SDK and its development CLI tools.

## Run the server

From the repository root, start the server directly:

```bash
python -m local_mcp_toolbox.server
```

The server uses stdio by default. When run directly, it waits for an MCP client to communicate over standard input/output. It is therefore expected that the terminal does not show a normal web address or interactive prompt. Stop a manually started process with Ctrl+C.

### Test interactively with MCP Inspector

After installing the project dependencies, run:

```bash
mcp dev src/local_mcp_toolbox/server.py
```

The MCP CLI starts the MCP Inspector, which can be used to list the available tools and call them with sample inputs. The Inspector is a Node.js application and requires `npx` to be available on PATH.

See the SDK's [Running your server guide](https://py.sdk.modelcontextprotocol.io/run/) for details about stdio and Inspector usage.

## Configure the notes directory

By default, the notes search tool reads from:

```text
data/notes/
```

The repository includes an example document at `data/notes/agentic_ai.md`.

To use another directory, set the `MCP_TOOLBOX_NOTES_DIR` environment variable to an absolute path before starting the server.

**Windows PowerShell:**

```powershell
$env:MCP_TOOLBOX_NOTES_DIR = "C:\Users\YourUser\Documents\my-notes"
python -m local_mcp_toolbox.server
```

**macOS / Linux:**

```bash
export MCP_TOOLBOX_NOTES_DIR="$HOME/my-notes"
python -m local_mcp_toolbox.server
```

Only regular Markdown and text files with `.md` or `.txt` extensions are searched. Files larger than 1 MB are skipped. Results use paths relative to the configured notes directory rather than exposing its absolute path.

## Connect to Claude Desktop

An MCP host launches the local server as a subprocess. For Claude Desktop, add an entry to its `claude_desktop_config.json` file.

Example Windows configuration:

```json
{
  "mcpServers": {
    "local-mcp-toolbox": {
      "command": "C:\\absolute\\path\\to\\local-mcp-toolbox\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "local_mcp_toolbox.server"
      ],
      "env": {
        "MCP_TOOLBOX_NOTES_DIR": "C:\\absolute\\path\\to\\local-mcp-toolbox\\data\\notes"
      }
    }
  }
}
```

Replace both example paths with the actual absolute paths on the machine running Claude Desktop. Use the Python interpreter from the virtual environment where this project was installed. Fully quit and restart Claude Desktop after changing its configuration.

The config file is typically located at `%APPDATA%\Claude\claude_desktop_config.json` on Windows. Follow the [official SDK real-host guide](https://py.sdk.modelcontextprotocol.io/get-started/real-host/) for host-specific setup and current guidance.

## Available MCP tools

### 1. `calculator`

Input:

```json
{
  "expression": "2 + 3 * (4 - 1)"
}
```

Example result:

```json
{
  "ok": true,
  "expression": "2 + 3 * (4 - 1)",
  "result": 11
}
```

Supported operators: `+`, `-`, `*`, `/`, `//`, `%`, and `**`, plus parentheses and numeric constants. The evaluator limits expression length, AST size, nesting depth, exponent magnitude, and numeric result magnitude.

### 2. `search_notes`

Input:

```json
{
  "query": "MCP server tools",
  "limit": 5
}
```

Example result:

```json
{
  "ok": true,
  "results_count": 1,
  "results": [
    {
      "source": "agentic_ai.md",
      "score": 3,
      "snippet": "The Model Context Protocol (MCP) provides a standard way..."
    }
  ]
}
```

The search uses case-insensitive keyword occurrence counts. It is a small lexical search utility, not semantic vector search. The result limit must be between 1 and 20.

### 3. `get_system_info`

Example result:

```json
{
  "os": "Windows",
  "os_release": "example-release",
  "architecture": "AMD64",
  "python_version": "3.11.0",
  "logical_cpu_count": 8
}
```

The values above are illustrative. Actual values are read from the machine running the MCP server.

## Run tests

Install development dependencies as shown above, then run:

```bash
python -m pytest -v
```

The current unit tests cover arithmetic behavior and safety restrictions, notes search and validation, relative result paths, missing notes directories, and the system-information response shape.

The unit tests call the tool helper functions directly. They do not replace an end-to-end MCP protocol test; use MCP Inspector to verify discovery and invocation through the protocol.

## Project structure

```text
local-mcp-toolbox/
├── data/
│   └── notes/
│       └── agentic_ai.md
├── src/
│   └── local_mcp_toolbox/
│       ├── __init__.py
│       ├── calculator.py
│       ├── notes.py
│       ├── server.py
│       └── system_info.py
├── tests/
│   └── test_tools.py
├── .gitignore
├── LICENSE
├── README.md
└── pyproject.toml
```

## Security and design notes

- The calculator parses arithmetic expressions into an AST and allows only selected numeric and operator nodes. It never evaluates arbitrary Python code.
- Notes search is read-only and limited to Markdown/text files under the configured notes directory.
- Notes results disclose relative file names, not absolute machine paths.
- System information is deliberately restricted to a small set of platform/runtime fields.
- The stdio transport uses stdout for MCP protocol messages. Avoid adding ordinary `print()` statements to server code; use logging to stderr for diagnostics.

This is a local development/portfolio project. Review the tools and configured notes directory before connecting the server to an MCP host.

## Current scope and possible extensions

The server currently exposes three synchronous tools over stdio. It does not provide a remote HTTP endpoint, authentication, persistent note indexing, semantic embeddings, or access controls beyond the configured local notes directory. Possible future extensions include more comprehensive tests using an in-memory MCP client, structured logging, configurable keyword ranking, and additional opt-in tools.

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.
