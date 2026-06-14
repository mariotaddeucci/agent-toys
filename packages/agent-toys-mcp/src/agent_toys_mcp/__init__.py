import logging

from fastmcp import FastMCP

from agent_toys_mcp.discovery import get_mcp_servers

logger = logging.getLogger(__name__)

app = FastMCP("agent-toys-mcp")


def _load_mcp_plugins() -> None:
    """Load all discovered MCP plugins and mount them to the main app."""
    servers = get_mcp_servers()
    
    if not servers:
        logger.warning(
            "No MCP plugins discovered. Install with 'uv sync --all-groups' "
            "to enable all MCPs, or install specific MCPs via their packages."
        )
    
    for server in servers:
        if server is None:
            continue
        
        logger.info(f"Mounting MCP: {server.name}")
        try:
            app.mount(server)
        except Exception as e:
            logger.error(f"Failed to mount MCP {server.name}: {e}")


# Load plugins on import
_load_mcp_plugins()


def main() -> None:
    app.run()

