from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger

from agent_toys_mcp.discovery import get_mcp_servers

logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[None]:
    servers = get_mcp_servers()
    if not servers:
        logger.warning(
            "No MCP plugins discovered. Install with 'uv sync --all-groups' "
            "to enable all MCPs, or install specific MCPs via their packages."
        )
    for mcp_server in servers:
        if mcp_server is None:
            continue
        logger.info(f"Mounting MCP: {mcp_server.name}")
        try:
            server.mount(mcp_server)
        except Exception:
            logger.exception(f"Failed to mount MCP {mcp_server.name}")
    yield


app = FastMCP("agent-toys-mcp", lifespan=_lifespan)


def main() -> None:
    app.run()
