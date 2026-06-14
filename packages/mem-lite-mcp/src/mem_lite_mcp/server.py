from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from fastmcp.prompts import Message, PromptResult
from pydantic import Field

from mem_lite_mcp.tools import MemoryTools

app = FastMCP("mem-lite")


def get_memory_tools() -> MemoryTools:
    return MemoryTools()


@app.tool()
async def save_memory(
    title: str = Field(description="Memory title", min_length=1, max_length=500),
    content: str = Field(description="Full memory content", min_length=1, max_length=50000),
    summary: str | None = Field(None, description="Optional memory summary", max_length=1000),
    tags: list[str] | None = Field(None, description="List of tags (will be normalized to kebab-case)"),
    tools: MemoryTools = Depends(get_memory_tools),
    ctx: Context = None,
) -> dict:
    """Create a new memory with auto-generated ULID. Tags are auto-normalized to kebab-case."""
    await ctx.debug(f"Starting save_memory: title='{title[:50]}...'")
    try:
        result = await tools.save_memory(title, content, summary, tags)
    except Exception as e:
        await ctx.error(f"Failed to save memory: {e!s}")
        raise
    else:
        await ctx.info(
            "Memory saved successfully",
            extra={
                "memory_id": result["memory_id"],
                "title": title,
                "tags_count": len(tags or []),
                "content_length": len(content),
            },
        )
        return result


@app.tool()
async def update_memory(
    memory_id: str = Field(description="Memory ID to update", min_length=26, max_length=26, pattern="^[0-9A-Z]{26}$"),
    title: str | None = Field(None, description="New memory title", min_length=1, max_length=500),
    content: str | None = Field(None, description="New memory content", min_length=1, max_length=50000),
    summary: str | None = Field(None, description="New memory summary", max_length=1000),
    tools: MemoryTools = Depends(get_memory_tools),
    ctx: Context = None,
) -> dict:
    """Update a memory's title, content, or summary. Pass None to leave a field unchanged."""
    await ctx.debug(f"Starting update_memory: memory_id={memory_id}")
    try:
        result = await tools.update_memory(memory_id, title, content, summary)
    except ValueError as e:
        await ctx.warning(f"Memory not found during update: {e!s}")
        raise
    except Exception as e:
        await ctx.error(f"Failed to update memory {memory_id}: {e!s}")
        raise
    else:
        await ctx.info(
            "Memory updated successfully", extra={"memory_id": memory_id, "updated_fields": result["updated_fields"]}
        )
        return result


@app.tool()
async def remove_memory(
    memory_id: str = Field(description="Memory ID to delete", min_length=26, max_length=26, pattern="^[0-9A-Z]{26}$"),
    tools: MemoryTools = Depends(get_memory_tools),
    ctx: Context = None,
) -> dict:
    """Delete a memory permanently with CASCADE cleanup of tags and relations."""
    await ctx.debug(f"Starting remove_memory: memory_id={memory_id}")
    try:
        result = await tools.remove_memory(memory_id)
    except Exception as e:
        await ctx.error(f"Failed to delete memory {memory_id}: {e!s}")
        raise
    else:
        await ctx.info(
            "Memory deleted successfully", extra={"memory_id": memory_id, "cascade_deleted": result["cascade_deleted"]}
        )
        return result


@app.tool()
async def search_memory(
    query: str = Field(description="Search query term(s)", min_length=1, max_length=200),
    tags_filter: list[str] | None = Field(None, description="List of tags to filter (AND logic - all must match)"),
    depth: int = Field(1, description="Depth of related memories to return (1 or 2)", ge=1, le=2),
    limit: int = Field(20, description="Maximum number of search results", ge=1, le=100),
    offset: int = Field(0, description="Pagination offset for results", ge=0),
    max_memories_per_result: int = Field(5, description="Maximum memories to return in results", ge=1, le=20),
    max_relations_per_memory: int = Field(5, description="Maximum related memories per search result", ge=1, le=10),
    tools: MemoryTools = Depends(get_memory_tools),
    ctx: Context = None,
) -> dict:
    """Search memories with FTS5 full-text search, tag filtering, and importance scoring.

    Scoring: FTS5 40% + Recency 30% + Relations 30%.
    """
    await ctx.debug(
        "Starting search_memory",
        extra={"query": query, "tags_filter": tags_filter, "depth": depth, "limit": limit, "offset": offset},
    )
    try:
        result = await tools.search_memory(
            query, tags_filter, depth, limit, offset, max_memories_per_result, max_relations_per_memory
        )
    except Exception as e:
        await ctx.error(f"Failed to search memories with query '{query}': {e!s}")
        raise
    else:
        await ctx.info(
            "Memory search completed",
            extra={
                "query": query,
                "total_matches": result["total_matches"],
                "returned": result["returned"],
                "query_time_ms": result["query_time_ms"],
            },
        )
        return result


@app.tool()
async def get_memory(
    memory_ids: list[str] = Field(description="List of memory IDs to retrieve", min_items=1, max_items=50),
    tools: MemoryTools = Depends(get_memory_tools),
    ctx: Context = None,
) -> dict:
    """Retrieve complete memory content by ID. Automatically updates last_read_at timestamp."""
    await ctx.debug(f"Starting get_memory: retrieving {len(memory_ids)} memories")
    try:
        result = await tools.get_memory(memory_ids)
    except Exception as e:
        await ctx.error(f"Failed to retrieve memories: {e!s}")
        raise
    else:
        await ctx.info(
            "Memories retrieved successfully", extra={"requested": len(memory_ids), "found": result["count"]}
        )
        return result


@app.tool()
async def add_tag(
    memory_id: str = Field(
        description="Memory ID to add tag to", min_length=26, max_length=26, pattern="^[0-9A-Z]{26}$"
    ),
    tag_name: str = Field(description="Tag name (will be normalized to kebab-case)", min_length=1, max_length=100),
    tools: MemoryTools = Depends(get_memory_tools),
    ctx: Context = None,
) -> dict:
    """Add a tag to a memory. Tags are auto-normalized to lowercase kebab-case. Idempotent operation."""
    await ctx.debug(f"Starting add_tag: memory_id={memory_id}, tag={tag_name}")
    try:
        result = await tools.add_tag(memory_id, tag_name)
    except Exception as e:
        await ctx.error(f"Failed to add tag to memory {memory_id}: {e!s}")
        raise
    else:
        await ctx.info(
            "Tag added to memory", extra={"memory_id": memory_id, "tag_name": tag_name, "tag_id": result["tag_id"]}
        )
        return result


@app.tool()
async def add_relation(
    memory_id_1: str = Field(description="First memory ID", min_length=26, max_length=26, pattern="^[0-9A-Z]{26}$"),
    memory_id_2: str = Field(description="Second memory ID", min_length=26, max_length=26, pattern="^[0-9A-Z]{26}$"),
    weight: float = Field(0.5, description="Relationship strength weight", ge=0.0, le=1.0),
    tools: MemoryTools = Depends(get_memory_tools),
    ctx: Context = None,
) -> dict:
    """Create bidirectional relationship between memories with weight 0.0 (weak) to 1.0 (strong).

    Updates weight if relationship already exists.
    """
    await ctx.debug(
        "Starting add_relation", extra={"memory_id_1": memory_id_1, "memory_id_2": memory_id_2, "weight": weight}
    )
    try:
        result = await tools.add_relation(memory_id_1, memory_id_2, weight)
    except ValueError as e:
        await ctx.warning(f"Invalid relation parameters: {e!s}")
        raise
    except Exception as e:
        await ctx.error(f"Failed to create relation between {memory_id_1} and {memory_id_2}: {e!s}")
        raise
    else:
        await ctx.info(
            "Relation created between memories",
            extra={
                "memory_id_1": memory_id_1,
                "memory_id_2": memory_id_2,
                "weight": weight,
                "relation_id": result["relation_id"],
            },
        )
        return result


@app.prompt(
    name="memory_maintenance",
    description="Comprehensive memory maintenance cycle (consolidate, compress, deduplicate, optimize, quality check)",
    tags={"maintenance"},
)
def memory_maintenance_prompt() -> PromptResult:
    messages = [
        Message(
            "Perform a complete memory maintenance cycle on the provided memories.\n\n"
            "Complete these operations in sequence:\n\n"
            "**1. SCANNING & DETECTION**\n"
            "- Identify duplicates (exact matches or 80%+ similar)\n"
            "- Flag outdated memories (30+ days without access)\n"
            "- Spot low-quality entries or formatting issues\n"
            "- Check for orphaned memories (unconnected to others)\n\n"
            "**2. CONSOLIDATION & COMPRESSION**\n"
            "- Merge duplicate memories into single authoritative version\n"
            "- Compress long memories into concise summaries (max 500 chars)\n"
            "- Keep only unique information across memory base\n"
            "- Preserve all unique insights and context\n\n"
            "**3. QUALITY IMPROVEMENT**\n"
            "- Ensure all titles are clear and descriptive\n"
            "- Verify content is well-organized and self-contained\n"
            "- Confirm summaries capture key insights\n"
            "- Validate tags are relevant and normalized\n"
            "- Fix grammatical or clarity issues\n\n"
            "**4. NETWORK OPTIMIZATION**\n"
            "- Strengthen connections between related concepts (weight 0.6+)\n"
            "- Remove weak or incorrect relationships (weight < 0.3)\n"
            "- Create missing links between related memories\n"
            "- Identify and connect knowledge clusters\n"
            "- Flag isolated memories for review\n\n"
            "**5. REPORTING**\n"
            "For the entire memory base, report:\n"
            "- Duplicates found and merged\n"
            "- Memories compressed (and old vs new sizes)\n"
            "- Quality issues fixed\n"
            "- New relationships created\n"
            "- Weak relationships removed\n"
            "- Orphaned memories (suggest keep/archive/delete)\n"
            "- Overall network health score (1-10)\n\n"
            "This single-pass maintenance keeps the knowledge base clean, "
            "well-organized, and optimally connected."
        )
    ]
    return PromptResult(messages=messages)


# Plugin entrypoint for agent-toys autodiscovery
def agent_toys_mcp():
    """Return this MCP for agent-toys plugin discovery."""
    return app
