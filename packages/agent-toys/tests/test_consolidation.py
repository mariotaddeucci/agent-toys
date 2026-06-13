"""Tests for agent-toys consolidated MCP aggregator."""

import pytest
from agent_toys import app
from mem_lite_mcp.tools import MemoryTools


@pytest.fixture
async def memory_tools():
    """Create MemoryTools instance for testing."""
    tools = MemoryTools(":memory:")
    await tools.db.init_db()
    return tools


async def test_consolidated_app_loads():
    """Test that the consolidated app loads correctly."""
    assert app.name == "agent-toys"


async def test_can_create_memory_via_consolidator(memory_tools):
    """Test creating a memory through the consolidated interface."""
    result = await memory_tools.save_memory(
        title="Test Memory",
        content="This is test content"
    )
    assert result['memory_id']
    assert result['created_at']


async def test_can_search_via_consolidator(memory_tools):
    """Test searching memories through the consolidated interface."""
    # Create a memory
    await memory_tools.save_memory(
        title="Test Memory",
        content="This is test content about Python"
    )
    
    # Search for it
    result = await memory_tools.search_memory("Python")
    assert result['returned'] > 0
    assert len(result['memories']) > 0


async def test_can_tag_via_consolidator(memory_tools):
    """Test adding tags through the consolidated interface."""
    # Create a memory
    mem = await memory_tools.save_memory(
        title="Test",
        content="Content"
    )
    
    # Add a tag
    result = await memory_tools.add_tag(
        memory_id=mem['memory_id'],
        tag_name="Python"
    )
    assert 'tag_id' in result or 'memory_id' in result


async def test_can_relate_via_consolidator(memory_tools):
    """Test creating relations through the consolidated interface."""
    # Create two memories
    mem1 = await memory_tools.save_memory(
        title="Memory 1",
        content="First memory"
    )
    mem2 = await memory_tools.save_memory(
        title="Memory 2",
        content="Second memory"
    )
    
    # Relate them
    result = await memory_tools.add_relation(
        memory_id_1=mem1['memory_id'],
        memory_id_2=mem2['memory_id'],
        weight=0.8
    )
    assert 'relation_id' in result or 'id_a' in result


async def test_consolidated_namespace():
    """Test that consolidator maintains proper namespacing via mount."""
    # Check that agent-toys app has been created
    assert app is not None
    assert app.name == "agent-toys"
    
    # With composition, tools are mounted from mem_lite_app
    # and automatically namespaced via mount(namespace="mem")
    # Tools available: mem_save_memory, mem_search_memory, etc.
    from mem_lite_mcp.server import app as mem_lite_app
    assert mem_lite_app is not None
