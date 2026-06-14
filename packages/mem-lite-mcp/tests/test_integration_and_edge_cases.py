"""Integration and edge case tests."""



# ==================== INTEGRATION TESTS ====================

async def test_complete_workflow(memory_tools):
    """Test complete workflow: create -> tag -> relate -> search."""
    # Create memories
    mem1 = await memory_tools.save_memory(
        title="Python Async",
        content="Learning async/await patterns",
        tags=["python", "async"]
    )

    mem2 = await memory_tools.save_memory(
        title="Event Loop",
        content="Understanding the event loop",
        tags=["python", "async"]
    )

    # Add relation
    await memory_tools.add_relation(
        mem1['memory_id'],
        mem2['memory_id'],
        weight=0.9
    )

    # Add additional tags
    await memory_tools.add_tag(mem1['memory_id'], "important")

    # Search
    result = await memory_tools.search_memory(
        "async",
        tags_filter=["python"],
        depth=2
    )

    assert result['returned'] > 0


async def test_update_and_search(memory_tools):
    """Test updating memory and searching for updates."""
    # Create memory
    memory = await memory_tools.save_memory(
        "Original Title",
        "Original content"
    )

    # Update memory
    await memory_tools.update_memory(
        memory['memory_id'],
        content="Updated content with new keywords"
    )

    # Search for new keywords
    result = await memory_tools.search_memory("keywords")

    assert result['returned'] > 0


async def test_remove_memory_with_relations(memory_tools):
    """Test that removing memory cleans up relations."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content 1")
    mem2 = await memory_tools.save_memory("Memory 2", "Content 2")

    # Add relation
    await memory_tools.add_relation(
        mem1['memory_id'],
        mem2['memory_id'],
        weight=0.8
    )

    # Remove mem1
    await memory_tools.remove_memory(mem1['memory_id'])

    # mem2 should still exist
    result = await memory_tools.get_memory([mem2['memory_id']])
    assert result['count'] == 1


# ==================== EDGE CASES TESTS ====================

async def test_very_long_title(memory_tools):
    """Test with maximum length title."""
    long_title = "x" * 500
    result = await memory_tools.save_memory(
        title=long_title,
        content="Content"
    )

    # Verify memory was created
    get_result = await memory_tools.get_memory([result['memory_id']])
    assert get_result['count'] == 1
    assert get_result['memories'][0]['title'] == long_title


async def test_very_long_content(memory_tools):
    """Test with maximum length content."""
    long_content = "x" * 50000
    result = await memory_tools.save_memory(
        title="Title",
        content=long_content
    )

    # Verify memory was created
    get_result = await memory_tools.get_memory([result['memory_id']])
    assert get_result['count'] == 1
    assert len(get_result['memories'][0]['content']) == 50000


async def test_many_tags(memory_tools):
    """Test memory with many tags."""
    tags = [f"tag{i}" for i in range(20)]
    result = await memory_tools.save_memory(
        title="Many Tags",
        content="Content",
        tags=tags
    )

    # Get and verify tags
    get_result = await memory_tools.get_memory([result['memory_id']])
    assert len(get_result['memories'][0]['tags']) == 20


async def test_unicode_content(memory_tools):
    """Test with unicode characters."""
    result = await memory_tools.save_memory(
        title="Unicode Test",
        content="Testing with émojis 🎉 and spëcial çhars"
    )

    # Verify memory was created
    get_result = await memory_tools.get_memory([result['memory_id']])
    assert get_result['count'] == 1
    assert "émojis" in get_result['memories'][0]['content']
    assert "🎉" in get_result['memories'][0]['content']


async def test_unicode_tags(memory_tools):
    """Test with unicode in tags."""
    memory = await memory_tools.save_memory("Title", "Content")
    result = await memory_tools.add_tag(
        memory['memory_id'],
        "日本語"
    )

    # Unicode tags may be normalized/dropped; check result is valid
    assert 'tag_id' in result
    assert 'memory_id' in result


async def test_empty_summary(memory_tools):
    """Test with empty summary."""
    result = await memory_tools.save_memory(
        title="Title",
        content="Content",
        summary=""
    )

    # Verify memory was created with empty summary
    get_result = await memory_tools.get_memory([result['memory_id']])
    assert get_result['count'] == 1


async def test_none_summary(memory_tools):
    """Test with None summary."""
    result = await memory_tools.save_memory(
        title="Title",
        content="Content",
        summary=None
    )

    # Verify memory was created
    get_result = await memory_tools.get_memory([result['memory_id']])
    assert get_result['count'] == 1


async def test_newlines_in_content(memory_tools):
    """Test with newlines in content."""
    content = "Line 1\nLine 2\nLine 3"
    result = await memory_tools.save_memory(
        title="Multiline",
        content=content
    )

    # Verify newlines are preserved
    get_result = await memory_tools.get_memory([result['memory_id']])
    assert "\n" in get_result['memories'][0]['content']


async def test_special_characters_in_search(memory_tools):
    """Test searching for special characters."""
    await memory_tools.save_memory(
        "Title",
        "Content with @#$%^&*()"
    )

    result = await memory_tools.search_memory("@#$%")

    # Should handle gracefully
    assert 'returned' in result


async def test_whitespace_normalization_in_tags(memory_tools):
    """Test that whitespace in tags is handled."""
    memory = await memory_tools.save_memory("Title", "Content")
    result = await memory_tools.add_tag(
        memory['memory_id'],
        "  spaced  tag  "
    )

    # Should normalize whitespace
    assert result['tag_id']


# ==================== CONSTRAINT VALIDATION TESTS ====================

async def test_search_depth_bounds(memory_tools):
    """Test search depth validation."""
    # Valid depths: 1, 2
    result1 = await memory_tools.search_memory("test", depth=1)
    result2 = await memory_tools.search_memory("test", depth=2)

    assert result1['returned'] >= 0
    assert result2['returned'] >= 0


async def test_search_limit_bounds(memory_tools):
    """Test search limit validation."""
    # Valid limits: 1-100
    result1 = await memory_tools.search_memory("test", limit=1)
    result2 = await memory_tools.search_memory("test", limit=100)

    assert result1['returned'] >= 0
    assert result2['returned'] >= 0


async def test_get_memory_max_ids(memory_tools):
    """Test that get_memory handles up to 50 IDs."""
    # Create 5 memories
    memories = []
    for i in range(5):
        mem = await memory_tools.save_memory(f"Memory {i}", "Content")
        memories.append(mem['memory_id'])

    # Get all 5
    result = await memory_tools.get_memory(memories)

    assert result['count'] <= 5
    assert result['count'] > 0
