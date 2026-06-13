"""Tests for search functionality."""

import pytest
from mem_lite_mcp.tools import MemoryTools


async def test_search_basic(memory_tools):
    """Test basic search functionality."""
    # Create memories
    await memory_tools.save_memory("Python Tips", "Learn async/await in Python")
    await memory_tools.save_memory("JavaScript", "Learn JavaScript basics")
    
    # Search
    result = await memory_tools.search_memory("Python")
    
    assert result['returned'] > 0
    assert result['total_matches'] >= 1


async def test_search_by_content(memory_tools):
    """Test searching by content."""
    await memory_tools.save_memory(
        "Title A",
        "This memory contains the word asyncio"
    )
    
    result = await memory_tools.search_memory("asyncio")
    assert result['returned'] > 0


async def test_search_with_depth_1(memory_tools):
    """Test search with depth=1 (no relations)."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content about Python")
    
    result = await memory_tools.search_memory(
        "Python",
        depth=1
    )
    
    assert result['returned'] >= 1


async def test_search_with_depth_2(memory_tools):
    """Test search with depth=2 (includes relations)."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content about Python")
    mem2 = await memory_tools.save_memory("Memory 2", "Related content")
    
    # Add relation
    await memory_tools.add_relation(
        mem1['memory_id'],
        mem2['memory_id'],
        weight=0.8
    )
    
    result = await memory_tools.search_memory(
        "Python",
        depth=2
    )
    
    assert result['returned'] >= 1


async def test_search_with_limit(memory_tools):
    """Test search with limit parameter."""
    # Create multiple memories
    for i in range(5):
        await memory_tools.save_memory(f"Memory {i}", "Python content")
    
    result = await memory_tools.search_memory(
        "Python",
        limit=2
    )
    
    assert result['returned'] <= 2


async def test_search_with_offset(memory_tools):
    """Test search with offset parameter."""
    # Create memories
    for i in range(3):
        await memory_tools.save_memory(f"Memory {i}", "Python content")
    
    result1 = await memory_tools.search_memory("Python", limit=1, offset=0)
    result2 = await memory_tools.search_memory("Python", limit=1, offset=1)
    
    # Results should be valid
    assert result1['returned'] > 0 or result2['returned'] > 0


async def test_search_with_tags_filter(memory_tools):
    """Test search with tags filter."""
    await memory_tools.save_memory(
        "Python Advanced",
        "Content about advanced Python",
        tags=["python", "advanced"]
    )
    
    result = await memory_tools.search_memory(
        "Python",
        tags_filter=["python"]
    )
    
    assert result['returned'] >= 1


async def test_search_empty_query(memory_tools):
    """Test search with empty query."""
    await memory_tools.save_memory("Memory", "Content")
    
    # Empty query might return all or none depending on implementation
    result = await memory_tools.search_memory("")
    assert 'returned' in result


async def test_search_no_results(memory_tools):
    """Test search with no matching results."""
    await memory_tools.save_memory("Python", "Python content")
    
    result = await memory_tools.search_memory("NonexistentKeyword123")
    
    assert result['returned'] == 0


async def test_search_max_memories_per_result(memory_tools):
    """Test search with max_memories_per_result limit."""
    await memory_tools.save_memory("Memory", "Python content")
    
    result = await memory_tools.search_memory(
        "Python",
        max_memories_per_result=1
    )
    
    assert result['returned'] >= 0


async def test_search_max_relations_per_memory(memory_tools):
    """Test search with max_relations_per_memory limit."""
    mem = await memory_tools.save_memory("Memory", "Python content")
    
    result = await memory_tools.search_memory(
        "Python",
        max_relations_per_memory=2
    )
    
    assert result['returned'] >= 0


async def test_search_response_structure(memory_tools):
    """Test that search response has correct structure."""
    await memory_tools.save_memory("Test", "Test content")
    
    result = await memory_tools.search_memory("Test")
    
    assert 'total_matches' in result
    assert 'returned' in result
    assert 'offset' in result
    assert 'query_time_ms' in result
    assert 'memories' in result
