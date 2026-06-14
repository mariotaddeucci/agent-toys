import tempfile
from pathlib import Path

import pytest

from mem_lite_mcp.tools import MemoryTools


@pytest.fixture
async def temp_db():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_path = tmp.name

    try:
        yield db_path
    finally:
        Path(db_path).unlink(missing_ok=True)


@pytest.fixture
async def memory_tools(temp_db):
    tools = MemoryTools(temp_db)
    yield tools


@pytest.fixture
async def sample_memory(memory_tools):
    return await memory_tools.save_memory(
        title="Test Memory",
        content="This is a test memory content",
        summary="Test summary",
        tags=["test", "example"]
    )
