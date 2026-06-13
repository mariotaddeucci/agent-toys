# agent-toys

Consolidated MCP aggregator that combines all MCPs from the workspace into a single unified connection point.

## Overview

**agent-toys** is a meta-MCP server that:
- Imports and re-exports all tools from workspace MCPs
- Provides a single connection point for agents
- Prefixes tool names with their origin package (e.g., `mem_*` for mem-lite)
- Combines all prompts under a unified namespace
- Maintains feature parity with individual MCPs

## Features

### Consolidated Tools

All tools are prefixed with their source MCP:

**Memory Management** (from `mem-lite-mcp`):
- `mem_save_memory` - Save new memory
- `mem_update_memory` - Update existing memory
- `mem_remove_memory` - Delete memory
- `mem_search_memory` - Full-text search memories
- `mem_get_memory` - Retrieve memory details
- `mem_add_tag` - Add tags to memory
- `mem_add_relation` - Link related memories

### Unified Prompts

**Memory** (from `mem-lite-mcp`):
- `mem_maintenance` - Complete memory maintenance cycle

## Installation

```bash
uv sync
```

## Running

```bash
# Via CLI
agent-toys

# Via Python module
python -m agent_toys

# Direct import and server.run()
uv run python -c "from agent_toys import app; app.run()"
```

## Architecture

```
agent-toys/
├── src/agent_toys/
│   ├── __init__.py        # Main app, imports and re-exports MCP tools/prompts
│   └── __main__.py        # CLI entry point
└── tests/                 # Test suite (future)
```

## How It Works

1. **Imports MCP Apps**: Imports `app` instances from workspace MCPs
2. **Re-registers Tools**: Creates wrapper tools with prefixed names
3. **Re-registers Prompts**: Creates wrapper prompts with prefixed names
4. **Single Connection**: Clients connect to `agent-toys` and access all tools

## Design Pattern

```python
# Example: mem-lite-mcp tool re-exported in agent-toys

@app.tool()
async def mem_save_memory(
    title: str,
    content: str,
    ...,
    tools: MemoryTools = Depends(get_memory_tools)
) -> dict:
    """[mem-lite] Save a new memory..."""
    return await tools.save_memory(title, content, ...)
```

**Naming Convention**:
- Tool prefix: MCP namespace (e.g., `mem_` for mem-lite)
- Function name: Original tool name
- Docstring prefix: `[MCP-name]` for clarity

## Adding a New MCP

To add a new MCP to the consolidator:

1. **Add dependency** to `agent-toys/pyproject.toml`:
   ```toml
   dependencies = [
       "mem-lite-mcp @ file://../../packages/mem-lite-mcp",
       "new-mcp @ file://../../packages/new-mcp",
   ]
   ```

2. **Import and wrap tools** in `src/agent_toys/__init__.py`:
   ```python
   from new_mcp.server import app as new_mcp_app
   from new_mcp.tools import NewMCPTools
   
   def get_new_mcp_tools() -> NewMCPTools:
       return NewMCPTools()
   
   @app.tool()
   async def new_my_tool(..., tools: NewMCPTools = Depends(get_new_mcp_tools)):
       return await tools.my_tool(...)
   ```

3. **Sync workspace**:
   ```bash
   uv sync
   ```

## Testing

```bash
# Run all tests
uv run pytest

# Test server imports
uv run python -c "from agent_toys import app; print(f'✓ {app.name} ready with {len(app._tools)} tools')"
```

## Dependencies

- `fastmcp>=3.4.2` - MCP server framework
- `mem-lite-mcp` - Memory management MCP
- Additional MCPs as added

## Development

All tools use FastMCP's `Depends()` for clean dependency injection, maintaining the same patterns as individual MCPs.

### Entry Points

- **CLI**: `agent-toys`
- **Module**: `python -m agent_toys`

### Workspace Context

Part of the `mem-lite` workspace:
```
mem-lite/
├── packages/mem-lite-mcp/    # Memory management MCP
├── packages/agent-toys/      # This package
└── pyproject.toml            # Workspace configuration
```

## Future Enhancements

- CLI for discovering available tools/prompts
- Tool/prompt filtering by tag or prefix
- Metric collection across MCPs
- Priority/rate limiting for tools
- Cross-MCP composition patterns
