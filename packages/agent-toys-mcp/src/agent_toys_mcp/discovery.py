"""MCP discovery system using entrypoints."""

import importlib.metadata
from typing import Any

from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)

HOOK_ENTRYPOINT = "agent_toys_mcp"


def get_mcp_servers() -> list[Any]:
    """Discover and load all MCP servers from entrypoints."""
    entry_points = importlib.metadata.entry_points()

    if hasattr(entry_points, "select"):
        agent_toys_eps = entry_points.select(group=HOOK_ENTRYPOINT)
    else:
        agent_toys_eps = entry_points.get(HOOK_ENTRYPOINT, [])  # type: ignore

    servers = []
    for ep in agent_toys_eps:
        try:
            func = ep.load()
            server = func()
            servers.append(server)
            logger.debug(f"Discovered MCP: {ep.name} ({server.name if hasattr(server, 'name') else '?'})")
        except Exception:
            logger.exception(f"Failed to load MCP plugin '{ep.name}'")

    if servers:
        logger.info(f"Discovered {len(servers)} MCP(s)")

    return servers
