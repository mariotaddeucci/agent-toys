"""FastMCP Server for Memory System."""

from fastmcp import FastMCP
from pydantic import Field
from typing import Optional, List
from .tools import MemoryTools


# Instantiate MCP app
app = FastMCP("mem-lite")

# Instantiate tools
_tools = None


def get_tools() -> MemoryTools:
    """Lazy initialization of tools."""
    global _tools
    if _tools is None:
        _tools = MemoryTools()
    return _tools


# ==================== TOOLS REGISTRATION ====================

@app.tool()
async def save_memory(
    title: str = Field(description="Memory title", min_length=1, max_length=500),
    content: str = Field(description="Full memory content", min_length=1, max_length=50000),
    summary: Optional[str] = Field(None, description="Optional memory summary", max_length=1000),
    tags: Optional[List[str]] = Field(None, description="List of tags (will be normalized to kebab-case)")
) -> dict:
    """Save a new memory with auto-generated ULID identifier.
    
    Creates a new memory entry with the provided title, content, and optional summary.
    Tags are automatically normalized to kebab-case format. The memory ID is auto-generated
    using ULID for sortability and built-in timestamps.
    """
    tools = get_tools()
    return await tools.save_memory(title, content, summary, tags)


@app.tool()
async def update_memory(
    memory_id: str = Field(description="Memory ID to update", min_length=26, max_length=26, pattern="^[0-9A-Z]{26}$"),
    title: Optional[str] = Field(None, description="New memory title", min_length=1, max_length=500),
    content: Optional[str] = Field(None, description="New memory content", min_length=1, max_length=50000),
    summary: Optional[str] = Field(None, description="New memory summary", max_length=1000)
) -> dict:
    """Update title, content, or summary of an existing memory.
    
    At least one field (title, content, or summary) must be provided for update.
    Passing None for a field leaves it unchanged.
    """
    tools = get_tools()
    return await tools.update_memory(memory_id, title, content, summary)


@app.tool()
async def remove_memory(
    memory_id: str = Field(description="Memory ID to delete", min_length=26, max_length=26, pattern="^[0-9A-Z]{26}$")
) -> dict:
    """Delete a memory permanently.
    
    Performs a hard delete of the memory and all associated data
    (tags, relations) with automatic CASCADE cleanup.
    This operation is irreversible.
    """
    tools = get_tools()
    return await tools.remove_memory(memory_id)


@app.tool()
async def search_memory(
    query: str = Field(description="Search query term(s)", min_length=1, max_length=200),
    tags_filter: Optional[List[str]] = Field(None, description="List of tags to filter (AND logic - all must match)"),
    depth: int = Field(1, description="Depth of related memories to return (1 or 2)", ge=1, le=2),
    limit: int = Field(20, description="Maximum number of search results", ge=1, le=100),
    offset: int = Field(0, description="Pagination offset for results", ge=0),
    max_memories_per_result: int = Field(5, description="Maximum memories to return in results", ge=1, le=20),
    max_relations_per_memory: int = Field(5, description="Maximum related memories per search result", ge=1, le=10)
) -> dict:
    """Search memories with full-text search, relation depth, and importance scoring.
    
    Returns memories matching the query, ranked by importance score combining:
    - FTS5 relevance (40%)
    - Recency/last-read time (30%)
    - Relation count (30%)
    
    Supports tag filtering with AND logic and configurable depth for related memories.
    Results include related memories up to the specified depth with their relationships.
    """
    tools = get_tools()
    return await tools.search_memory(query, tags_filter, depth, limit, offset,
                                     max_memories_per_result, max_relations_per_memory)


@app.tool()
async def get_memory(
    memory_ids: List[str] = Field(description="List of memory IDs to retrieve", min_items=1, max_items=50)
) -> dict:
    """Retrieve multiple memories with complete content and metadata.
    
    Fetches the full content of specified memories. Updates last_read_at timestamp
    for all retrieved memories. Returns memories in the order requested, excluding
    any IDs that don't exist.
    """
    tools = get_tools()
    return await tools.get_memory(memory_ids)


@app.tool()
async def add_tag(
    memory_id: str = Field(description="Memory ID to add tag to", min_length=26, max_length=26, pattern="^[0-9A-Z]{26}$"),
    tag_name: str = Field(description="Tag name (will be normalized to kebab-case)", min_length=1, max_length=100)
) -> dict:
    """Add a tag to an existing memory.
    
    Tags are automatically normalized to lowercase kebab-case format (e.g., "Machine Learning" -> "machine-learning").
    If the tag already exists on the memory, this operation is idempotent (no duplicate tags).
    """
    tools = get_tools()
    return await tools.add_tag(memory_id, tag_name)


@app.tool()
async def add_relation(
    memory_id_1: str = Field(description="First memory ID", min_length=26, max_length=26, pattern="^[0-9A-Z]{26}$"),
    memory_id_2: str = Field(description="Second memory ID", min_length=26, max_length=26, pattern="^[0-9A-Z]{26}$"),
    weight: float = Field(0.5, description="Relationship strength weight", ge=0.0, le=1.0)
) -> dict:
    """Create a bidirectional relationship between two memories.
    
    Creates or updates a relationship with a weight value between 0.0 (weak) and 1.0 (strong).
    Relationships are bidirectional - relating A to B also relates B to A.
    If the relationship already exists, it updates the weight.
    Cannot create self-relations (same memory ID for both arguments).
    """
    tools = get_tools()
    return await tools.add_relation(memory_id_1, memory_id_2, weight)
