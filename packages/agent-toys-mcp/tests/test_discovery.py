"""Tests for MCP discovery system."""

from agent_toys_mcp.discovery import get_mcp_servers


def test_get_mcp_servers_returns_list():
    """Test that get_mcp_servers returns a list."""
    servers = get_mcp_servers()
    assert isinstance(servers, list)


def test_get_mcp_servers_can_be_empty():
    """Test that get_mcp_servers can return empty list if no MCPs installed."""
    # This test just verifies the function doesn't crash
    servers = get_mcp_servers()
    # Could be empty or have servers depending on installation
    assert isinstance(servers, list)


def test_mcp_entrypoint_is_registered():
    """Test that mem-lite-mcp has the agent_toys_mcp entrypoint registered."""
    import importlib.metadata

    # Check if mem-lite-mcp entrypoint exists
    entry_points = importlib.metadata.entry_points()

    # Look for agent_toys_mcp group
    if hasattr(entry_points, "select"):  # Python 3.10+
        agent_toys_mcp_eps = entry_points.select(group="agent_toys_mcp")
    else:  # Python 3.9 and below
        agent_toys_mcp_eps = entry_points.get("agent_toys_mcp", [])

    # There should be at least one entry (mem-lite)
    assert len(list(agent_toys_mcp_eps)) > 0


def test_get_mcp_servers_discovers_mem_lite():
    """Test that get_mcp_servers discovers mem-lite-mcp when installed."""
    servers = get_mcp_servers()

    # If servers exist, at least one should be mem-lite
    if servers:
        assert any(s.name == "mem-lite" for s in servers)


def test_mcp_servers_have_required_attributes():
    """Test that discovered MCP servers have required FastMCP attributes."""
    servers = get_mcp_servers()

    for server in servers:
        # All FastMCP instances should have these attributes
        assert hasattr(server, "name")
        assert hasattr(server, "mount")
        assert hasattr(server, "run")

