# agent-toys

Consolidated MCP aggregator that combines all MCPs from the workspace into a single unified connection point using FastMCP composition.

## Overview

**agent-toys** is a meta-MCP server that:
- Uses FastMCP `mount()` to compose multiple MCPs
- Automatically namespaces tools from child MCPs to avoid conflicts
- Provides a single connection point for agents
- Maintains live links to mounted servers (tools added later are immediately visible)
- Zero duplication - no re-implementation of tools

## Architecture

```python
app = FastMCP("agent-toys")
app.mount(mem_lite_app, namespace="mem")
# Tools automatically namespaced: mem_save_memory, mem_search_memory, etc.
```

## Features

### Memory Management Tools (from `mem-lite-mcp`)

All tools are automatically prefixed with `mem_` namespace:
- `mem_save_memory` - Save new memory
- `mem_update_memory` - Update existing memory
- `mem_remove_memory` - Delete memory
- `mem_search_memory` - Full-text search memories
- `mem_get_memory` - Retrieve memory details
- `mem_add_tag` - Add tags to memory
- `mem_add_relation` - Link related memories

### Unified Prompts

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

## How Composition Works

With FastMCP `mount()`, **no tool re-implementation** is needed:

```python
from fastmcp import FastMCP
from mem_lite_mcp.server import app as mem_lite_app

app = FastMCP("agent-toys")
app.mount(mem_lite_app, namespace="mem")
# Done! All tools from mem_lite_app are now available as mem_*
```

**Benefits:**
- Single source of truth (tools defined once in mem-lite-mcp)
- Automatic namespace conflict resolution
- Live binding (tools added to mem_lite_app later are immediately visible)
- Zero code duplication
- Minimal boilerplate

## Namespacing

| Original Tool (mem-lite-mcp) | Namespaced in agent-toys |
|------------------------------|--------------------------|
| `save_memory`                | `mem_save_memory`        |
| `search_memory`              | `mem_search_memory`      |
| `get_memory`                 | `mem_get_memory`         |
| `add_tag`                    | `mem_add_tag`            |
| `add_relation`               | `mem_add_relation`       |

## Adding a New MCP

To add a new MCP to the consolidator:

1. **Create the MCP package** (e.g., `packages/new-mcp/`)
2. **Add to agent-toys** in `src/agent_toys/__init__.py`:
   ```python
   from fastmcp import FastMCP
   from mem_lite_mcp.server import app as mem_lite_app
   from new_mcp.server import app as new_mcp_app
   
   app = FastMCP("agent-toys")
   app.mount(mem_lite_app, namespace="mem")
   app.mount(new_mcp_app, namespace="new")
   ```

3. **Add dependency** to `agent-toys/pyproject.toml`:
   ```toml
   dependencies = [
       "fastmcp>=3.4.2",
       "mem-lite-mcp",
       "new-mcp",
   ]
   ```

4. **Sync workspace**:
   ```bash
   uv sync
   ```

That's it! No tool re-wrapping needed.

## Testing

```bash
# Run consolidation tests
uv run pytest tests/

# Test server composition
uv run python -c "from agent_toys import app; print(f'✓ {app.name} ready')"
```

## Composition Pattern

This follows FastMCP's composition pattern exactly:

```
Clients (Claude, etc.)
    ↓
agent-toys (parent)
    ├── mount(mem_lite_app, namespace="mem")
    │   └─ mem_save_memory, mem_search_memory, etc.
    ├── mount(future_app, namespace="future")
    │   └─ future_*, ...
    └── mount(another_app, namespace="another")
        └─ another_*, ...
```

## Architecture

```
mem-lite/
├── packages/
│   ├── mem-lite-mcp/
│   │   └── src/mem_lite_mcp/server.py (defines app + tools)
│   └── agent-toys/
│       └── src/agent_toys/__init__.py (mounts mem_lite_app)
└── pyproject.toml (workspace)
```

## Entry Points

- **CLI**: `agent-toys`
- **Module**: `python -m agent_toys`

## Dependencies

- `fastmcp>=3.4.2` - MCP server framework
- `mem-lite-mcp` - Memory management MCP

## Key Benefits of Composition

✅ **No Duplication** - Tools defined once, composed multiple times
✅ **Namespace Isolation** - No conflicts between MCPs
✅ **Live Binding** - Tools added to child MCPs are immediately visible
✅ **Minimal Boilerplate** - Just mount and you're done
✅ **Scalable** - Add MCPs without code duplication
✅ **Maintainable** - Changes to tools only need to happen in one place

## Related

- See [gofastmcp.com/servers/composition](https://gofastmcp.com/servers/composition) for composition documentation
- See [packages/mem-lite-mcp/README.md](../mem-lite-mcp/README.md) for memory MCP details
