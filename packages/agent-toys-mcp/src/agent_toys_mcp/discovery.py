"""MCP discovery system using pluggy entrypoints.

This module handles automatic discovery and loading of MCP servers
that are compatible with agent-toys through setuptools entrypoints.

MCPs are discovered by looking for functions registered in the
'agent_toys_mcp' entrypoint group. Each function should return a
FastMCP application instance.
"""

import importlib.metadata
import logging
from typing import Any

logger = logging.getLogger(__name__)

HOOK_ENTRYPOINT = "agent_toys_mcp"


def get_mcp_servers() -> list[Any]:
    """Get all MCP servers from discovered entrypoints.

    Discovers all MCP servers by loading functions registered in the
    'agent_toys_mcp' entrypoint group and calling them to get FastMCP
    application instances.

    Returns:
        List of FastMCP application instances discovered from entrypoints.

    Example:
        >>> servers = get_mcp_servers()
        >>> for server in servers:
        ...     print(f"Found MCP: {server.name}")
    """
    entry_points = importlib.metadata.entry_points()
    
    # Handle both Python 3.10+ (with .select()) and 3.9 (with .get())
    if hasattr(entry_points, "select"):  # Python 3.10+
        agent_toys_eps = entry_points.select(group=HOOK_ENTRYPOINT)
    else:  # Python 3.9 and below
        agent_toys_eps = entry_points.get(HOOK_ENTRYPOINT, [])
    
    servers = []
    for ep in agent_toys_eps:
        try:
            # Load the entrypoint function
            func = ep.load()
            
            # Call it to get the MCP server
            server = func()
            servers.append(server)
            
            logger.debug(f"Discovered MCP: {ep.name} ({server.name if hasattr(server, 'name') else '?'})")
        except Exception as e:
            logger.error(f"Failed to load MCP plugin '{ep.name}': {e}")
            import traceback
            traceback.print_exc()
    
    if servers:
        logger.info(f"Discovered {len(servers)} MCP(s)")
    
    return servers
