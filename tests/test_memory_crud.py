"""Tests for memory operations (save, update, get, remove)."""

import pytest
from src.mem_lite.tools import MemoryTools


# ==================== SAVE MEMORY TESTS ====================

async def test_save_memory_basic(memory_tools):
    """Test saving a basic memory."""
    result = await memory_tools.save_memory(
        title="My Memory",
        content="This is the content"
    )
    
    assert result['memory_id']
    assert len(result['memory_id']) == 26  # ULID format
    assert result['title'] == "My Memory"
    assert result['created_at']


async def test_save_memory_with_summary(memory_tools):
    """Test saving memory with summary."""
    result = await memory_tools.save_memory(
        title="Memory with Summary",
        content="Full content here",
        summary="Brief summary"
    )
    
    assert result['memory_id']
    assert result['title'] == "Memory with Summary"


async def test_save_memory_with_tags(memory_tools):
    """Test saving memory with tags."""
    result = await memory_tools.save_memory(
        title="Tagged Memory",
        content="Content",
        tags=["Python", "AsyncIO"]
    )
    
    # Tags should be in tags_added
    assert 'tags_added' in result
    assert len(result['tags_added']) == 2


async def test_save_memory_empty_tags(memory_tools):
    """Test saving memory without tags."""
    result = await memory_tools.save_memory(
        title="No Tags",
        content="Content"
    )
    
    assert 'tags_added' in result


async def test_save_memory_max_content_length(memory_tools):
    """Test saving memory with maximum content length."""
    max_content = "x" * 50000
    result = await memory_tools.save_memory(
        title="Max Content",
        content=max_content
    )
    
    assert result['memory_id']


# ==================== UPDATE MEMORY TESTS ====================

async def test_update_memory_title(sample_memory, memory_tools):
    """Test updating memory title."""
    memory_id = sample_memory['memory_id']
    result = await memory_tools.update_memory(
        memory_id=memory_id,
        title="Updated Title"
    )
    
    assert result['memory_id'] == memory_id
    assert 'title' in result['updated_fields']


async def test_update_memory_content(sample_memory, memory_tools):
    """Test updating memory content."""
    memory_id = sample_memory['memory_id']
    result = await memory_tools.update_memory(
        memory_id=memory_id,
        content="New content"
    )
    
    assert result['memory_id'] == memory_id
    assert 'content' in result['updated_fields']


async def test_update_memory_summary(sample_memory, memory_tools):
    """Test updating memory summary."""
    memory_id = sample_memory['memory_id']
    result = await memory_tools.update_memory(
        memory_id=memory_id,
        summary="New summary"
    )
    
    assert result['memory_id'] == memory_id
    assert 'summary' in result['updated_fields']


async def test_update_memory_all_fields(sample_memory, memory_tools):
    """Test updating all memory fields."""
    memory_id = sample_memory['memory_id']
    result = await memory_tools.update_memory(
        memory_id=memory_id,
        title="New Title",
        content="New content",
        summary="New summary"
    )
    
    assert result['memory_id'] == memory_id
    assert 'title' in result['updated_fields']
    assert 'content' in result['updated_fields']
    assert 'summary' in result['updated_fields']


# ==================== GET MEMORY TESTS ====================

async def test_get_memory_single(sample_memory, memory_tools):
    """Test retrieving a single memory."""
    memory_id = sample_memory['memory_id']
    result = await memory_tools.get_memory([memory_id])
    
    assert result['count'] == 1
    assert len(result['memories']) == 1
    assert result['memories'][0]['id'] == memory_id


async def test_get_memory_multiple(memory_tools):
    """Test retrieving multiple memories."""
    # Create multiple memories
    mem1 = await memory_tools.save_memory("Memory 1", "Content 1")
    mem2 = await memory_tools.save_memory("Memory 2", "Content 2")
    mem3 = await memory_tools.save_memory("Memory 3", "Content 3")
    
    result = await memory_tools.get_memory(
        [mem1['memory_id'], mem2['memory_id'], mem3['memory_id']]
    )
    
    assert result['count'] == 3
    assert len(result['memories']) == 3


async def test_get_memory_updates_last_read(sample_memory, memory_tools):
    """Test that get_memory updates last_read_at."""
    memory_id = sample_memory['memory_id']
    
    result = await memory_tools.get_memory([memory_id])
    last_read = result['memories'][0]['last_read_at']
    
    # last_read_at should be set
    assert last_read is not None


async def test_get_memory_nonexistent(memory_tools):
    """Test getting non-existent memory."""
    result = await memory_tools.get_memory(["01ARZ3NDEKTSV4RRFFQ69G5FAV"])
    
    assert result['count'] == 0
    assert result['memories'] == []


# ==================== REMOVE MEMORY TESTS ====================

async def test_remove_memory(sample_memory, memory_tools):
    """Test removing a memory."""
    memory_id = sample_memory['memory_id']
    
    # Verify it exists
    get_result = await memory_tools.get_memory([memory_id])
    assert get_result['count'] == 1
    
    # Remove it
    result = await memory_tools.remove_memory(memory_id)
    assert result['deleted'] is True
    
    # Verify it's gone
    get_result = await memory_tools.get_memory([memory_id])
    assert get_result['count'] == 0


async def test_remove_memory_with_tags(memory_tools):
    """Test removing memory cascades tag deletion."""
    # Create memory with tags
    memory = await memory_tools.save_memory(
        title="Memory with Tags",
        content="Content",
        tags=["important", "review"]
    )
    
    # Remove memory
    result = await memory_tools.remove_memory(memory['memory_id'])
    assert result['deleted'] is True
    
    # Memory should be gone
    get_result = await memory_tools.get_memory([memory['memory_id']])
    assert get_result['count'] == 0


async def test_remove_memory_nonexistent(memory_tools):
    """Test removing non-existent memory."""
    # Should return deletion info even if not found
    result = await memory_tools.remove_memory("01ARZ3NDEKTSV4RRFFQ69G5FAV")
    assert 'deleted' in result
    assert 'cascade_deleted' in result
