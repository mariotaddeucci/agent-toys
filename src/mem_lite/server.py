"""FastMCP Server for Memory System."""

from fastmcp import FastMCP
from .tools import MemoryTools
from typing import Optional


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
async def save_memory(title: str, content: str, summary: Optional[str] = None,
                     tags: Optional[list] = None) -> dict:
    """Save a new memory.
    
    Args:
        title: Memory title
        content: Full content
        summary: Optional summary
        tags: List of tags (will be normalized to kebab-case)
    
    Returns:
        memory_id, created_at, title, tags_added
    """
    tools = get_tools()
    return await tools.save_memory(title, content, summary, tags)


@app.tool()
async def update_memory(memory_id: str, title: Optional[str] = None,
                       content: Optional[str] = None,
                       summary: Optional[str] = None) -> dict:
    """Update title/content/summary of a memory.
    
    Args:
        memory_id: Memory ID to update
        title: New title (optional)
        content: New content (optional)
        summary: New summary (optional)
    
    Returns:
        memory_id, updated_fields
    """
    tools = get_tools()
    return await tools.update_memory(memory_id, title, content, summary)


@app.tool()
async def remove_memory(memory_id: str) -> dict:
    """Delete a memory (hard delete with CASCADE cleanup).
    
    Args:
        memory_id: Memory ID to delete
    
    Returns:
        memory_id, deleted status, cascade_deleted counts
    """
    tools = get_tools()
    return await tools.remove_memory(memory_id)


@app.tool()
async def search_memory(query: str, tags_filter: Optional[list] = None,
                       depth: int = 1, limit: int = 20, offset: int = 0,
                       max_memories_per_result: int = 5,
                       max_relations_per_memory: int = 5) -> dict:
    """Search memories with full-text search + related memories + importance scoring.
    
    Returns memories matching the query, with importance scores
    and related memories up to 2 levels of depth.
    
    Args:
        query: Search term
        tags_filter: Tags to filter (AND logic)
        depth: Depth of relations (1 or 2)
        limit: Maximum number of results (default 20)
        offset: Offset for pagination (default 0)
        max_memories_per_result: Maximum memories to return (default 5)
        max_relations_per_memory: Maximum related memories per result (default 5)
    
    Returns:
        total_matches, returned, offset, memories with scores and related
    """
    tools = get_tools()
    return await tools.search_memory(query, tags_filter, depth, limit, offset,
                                     max_memories_per_result, max_relations_per_memory)


@app.tool()
async def get_memory(memory_ids: list) -> dict:
    """Get multiple memories with complete content.
    
    Args:
        memory_ids: List of memory IDs
    
    Returns:
        memories (with complete content), count
    """
    tools = get_tools()
    return await tools.get_memory(memory_ids)


@app.tool()
async def add_tag(memory_id: str, tag_name: str) -> dict:
    """Add a tag to a memory.
    
    Args:
        memory_id: Memory ID
        tag_name: Tag name (will be normalized to kebab-case)
    
    Returns:
        tag_id, memory_id, created_at
    """
    tools = get_tools()
    return await tools.add_tag(memory_id, tag_name)


@app.tool()
async def add_relation(memory_id_1: str, memory_id_2: str,
                      weight: float = 0.5) -> dict:
    """Add bidirectional relationship between two memories.
    
    Args:
        memory_id_1: First ID
        memory_id_2: Second ID
        weight: Relationship weight (0-1, default 0.5)
    
    Returns:
        relation_id, id_a, id_b, weight, created_at, bidirectional=true
    """
    tools = get_tools()
    return await tools.add_relation(memory_id_1, memory_id_2, weight)
