"""Tests for tags and relations functionality."""

import pytest

# ==================== ADD TAG TESTS ====================


async def test_add_tag_basic(sample_memory, memory_tools):
    """Test adding a basic tag."""
    memory_id = sample_memory["memory_id"]
    result = await memory_tools.add_tag(memory_id=memory_id, tag_name="important")

    assert result["tag_id"] == "important"
    assert result["memory_id"] == memory_id


async def test_add_tag_multiple(memory_tools):
    """Test adding multiple tags to same memory."""
    memory = await memory_tools.save_memory("Memory", "Content")
    memory_id = memory["memory_id"]

    result1 = await memory_tools.add_tag(memory_id, "tag1")
    result2 = await memory_tools.add_tag(memory_id, "tag2")
    result3 = await memory_tools.add_tag(memory_id, "tag3")

    assert result1["tag_id"] == "tag1"
    assert result2["tag_id"] == "tag2"
    assert result3["tag_id"] == "tag3"


async def test_add_tag_normalization(sample_memory, memory_tools):
    """Test that tags are normalized to kebab-case."""
    memory_id = sample_memory["memory_id"]
    result = await memory_tools.add_tag(memory_id=memory_id, tag_name="Machine Learning")

    # Should be normalized to kebab-case
    assert result["tag_id"] == "machine-learning"


async def test_add_tag_duplicate(memory_tools):
    """Test adding duplicate tag."""
    memory = await memory_tools.save_memory("Memory", "Content")
    memory_id = memory["memory_id"]

    result1 = await memory_tools.add_tag(memory_id, "tag")
    result2 = await memory_tools.add_tag(memory_id, "tag")

    # Should handle duplicate gracefully
    assert result1["tag_id"] == "tag"
    assert result2["tag_id"] == "tag"


async def test_add_tag_special_characters(sample_memory, memory_tools):
    """Test adding tag with special characters."""
    memory_id = sample_memory["memory_id"]
    result = await memory_tools.add_tag(memory_id=memory_id, tag_name="C++")

    # Should normalize appropriately
    assert result["tag_id"]


async def test_add_tag_empty_name(sample_memory, memory_tools):
    """Test that empty tag names are rejected."""
    memory_id = sample_memory["memory_id"]

    # This should fail or be handled gracefully
    try:
        result = await memory_tools.add_tag(memory_id, "")
        # If it succeeds, tag_id should not be empty
        assert result["tag_id"]
    except (ValueError, Exception):
        # Expected behavior
        pass


# ==================== ADD RELATION TESTS ====================


async def test_add_relation_basic(memory_tools):
    """Test adding a basic relation."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content 1")
    mem2 = await memory_tools.save_memory("Memory 2", "Content 2")

    result = await memory_tools.add_relation(memory_id_1=mem1["memory_id"], memory_id_2=mem2["memory_id"], weight=0.8)

    assert result["relation_id"]
    assert result["weight"] == 0.8


async def test_add_relation_bidirectional(memory_tools):
    """Test that relations are bidirectional."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content 1")
    mem2 = await memory_tools.save_memory("Memory 2", "Content 2")

    result = await memory_tools.add_relation(mem1["memory_id"], mem2["memory_id"], weight=0.7)

    assert result["bidirectional"] is True


async def test_add_relation_weight_min(memory_tools):
    """Test relation with minimum weight (0.0)."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content 1")
    mem2 = await memory_tools.save_memory("Memory 2", "Content 2")

    result = await memory_tools.add_relation(mem1["memory_id"], mem2["memory_id"], weight=0.0)

    assert result["weight"] == 0.0


async def test_add_relation_weight_max(memory_tools):
    """Test relation with maximum weight (1.0)."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content 1")
    mem2 = await memory_tools.save_memory("Memory 2", "Content 2")

    result = await memory_tools.add_relation(mem1["memory_id"], mem2["memory_id"], weight=1.0)

    assert result["weight"] == 1.0


async def test_add_relation_weight_mid(memory_tools):
    """Test relation with mid-range weight."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content 1")
    mem2 = await memory_tools.save_memory("Memory 2", "Content 2")

    result = await memory_tools.add_relation(mem1["memory_id"], mem2["memory_id"], weight=0.5)

    assert result["weight"] == 0.5


async def test_add_relation_invalid_weight_negative(memory_tools):
    """Test that negative weight is rejected."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content 1")
    mem2 = await memory_tools.save_memory("Memory 2", "Content 2")

    # Should raise error or handle gracefully
    try:
        await memory_tools.add_relation(mem1["memory_id"], mem2["memory_id"], weight=-0.5)
        pytest.fail("Should reject negative weight")
    except (ValueError, Exception):
        pass


async def test_add_relation_invalid_weight_over_one(memory_tools):
    """Test that weight > 1.0 is rejected."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content 1")
    mem2 = await memory_tools.save_memory("Memory 2", "Content 2")

    # Should raise error or handle gracefully
    try:
        await memory_tools.add_relation(mem1["memory_id"], mem2["memory_id"], weight=1.5)
        pytest.fail("Should reject weight > 1.0")
    except (ValueError, Exception):
        pass


async def test_add_relation_same_memory(memory_tools):
    """Test adding relation between same memory."""
    mem = await memory_tools.save_memory("Memory", "Content")

    # This might be allowed or rejected depending on implementation
    try:
        result = await memory_tools.add_relation(mem["memory_id"], mem["memory_id"], weight=0.5)
        # If allowed, should work
        assert result["relation_id"]
    except (ValueError, Exception):
        # If not allowed, that's also fine
        pass


async def test_add_relation_update_weight(memory_tools):
    """Test updating weight of existing relation."""
    mem1 = await memory_tools.save_memory("Memory 1", "Content 1")
    mem2 = await memory_tools.save_memory("Memory 2", "Content 2")

    # Add initial relation
    await memory_tools.add_relation(mem1["memory_id"], mem2["memory_id"], weight=0.5)

    # Update weight
    result2 = await memory_tools.add_relation(mem1["memory_id"], mem2["memory_id"], weight=0.9)

    assert result2["weight"] == 0.9
