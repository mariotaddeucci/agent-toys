import pytest
from agent_toys_mcp import app
from mem_lite_mcp.tools import MemoryTools


@pytest.fixture
async def memory_tools():
    tools = MemoryTools(":memory:")
    await tools.db.init_db()
    return tools


async def test_consolidated_app_loads():
    assert app.name == "agent-toys-mcp"


async def test_can_create_memory_via_consolidator(memory_tools):
    result = await memory_tools.save_memory(
        title="Test Memory",
        content="This is test content"
    )
    assert result['memory_id']
    assert result['created_at']


async def test_can_search_via_consolidator(memory_tools):
    await memory_tools.save_memory(
        title="Test Memory",
        content="This is test content about Python"
    )
    
    result = await memory_tools.search_memory("Python")
    assert result['returned'] > 0
    assert len(result['memories']) > 0


async def test_can_tag_via_consolidator(memory_tools):
    mem = await memory_tools.save_memory(
        title="Test",
        content="Content"
    )
    
    result = await memory_tools.add_tag(
        memory_id=mem['memory_id'],
        tag_name="Python"
    )
    assert 'tag_id' in result or 'memory_id' in result


async def test_can_relate_via_consolidator(memory_tools):
    mem1 = await memory_tools.save_memory(
        title="Memory 1",
        content="First memory"
    )
    mem2 = await memory_tools.save_memory(
        title="Memory 2",
        content="Second memory"
    )
    
    result = await memory_tools.add_relation(
        memory_id_1=mem1['memory_id'],
        memory_id_2=mem2['memory_id'],
        weight=0.8
    )
    assert 'relation_id' in result or 'id_a' in result


async def test_consolidated_namespace():
    assert app is not None
    assert app.name == "agent-toys-mcp"
    
    from mem_lite_mcp.server import app as mem_lite_app
    assert mem_lite_app is not None
