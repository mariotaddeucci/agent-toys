"""Agent Toys: Consolidated MCP Aggregator

Combines all MCPs from the workspace into a single unified connection point
using FastMCP composition with mount() and namespacing.
"""

from fastmcp import FastMCP

# Import sub-servers from workspace packages
from mem_lite_mcp.server import app as mem_lite_app


# Create the consolidated MCP app
app = FastMCP("agent-toys")

# Mount mem-lite-mcp with namespace
app.mount(mem_lite_app, namespace="mem")


# ==================== ENTRY POINT ====================

def main():
    """Entry point for agent-toys MCP server."""
    app.run()


if __name__ == "__main__":
    main()
