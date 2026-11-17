# Agentic AI Notes

Agentic AI systems use models and software tools to pursue goals through multiple steps. A typical agent loop interprets a task, selects a tool, sends structured arguments, receives the result, and decides what to do next.

The Model Context Protocol (MCP) provides a standard way for an AI host to discover and call tools exposed by an MCP server. An MCP server can run locally over standard input and output (stdio), or expose a network endpoint using Streamable HTTP.

A useful MCP tool should have a clear name, a concise description, typed inputs, predictable outputs, and input validation. Tools should return only the information needed for the task and should avoid exposing secrets or unrelated local system details.
