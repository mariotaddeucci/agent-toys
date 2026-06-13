"""Pytest configuration and fixtures for mem-lite tests."""

import asyncio
import tempfile
from pathlib import Path
import pytest
from mem_lite_mcp.tools import MemoryTools
from mem_lite_mcp.db import Database


@pytest.fixture
async def temp_db():
    """Fixture: temporary in-memory database for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_path = tmp.name
    
    try:
        yield db_path
    finally:
        # Cleanup
        Path(db_path).unlink(missing_ok=True)


@pytest.fixture
async def memory_tools(temp_db):
    """Fixture: MemoryTools instance with temporary database."""
    tools = MemoryTools(temp_db)
    yield tools


@pytest.fixture
async def sample_memory(memory_tools):
    """Fixture: create a sample memory for testing."""
    result = await memory_tools.save_memory(
        title="Test Memory",
        content="This is a test memory content",
        summary="Test summary",
        tags=["test", "example"]
    )
    return result
