# agent-toys-mcp

Consolidated MCP aggregator that automatically discovers and composes all MCPs compatible with agent-toys-mcp using setuptools entrypoints and FastMCP composition.

## Overview

**agent-toys-mcp** is a meta-MCP server that:
- **Auto-discovers MCPs** via setuptools entrypoints (`agent_toys_mcp_mcp` group)
- Uses FastMCP `mount()` to compose multiple MCPs
- Automatically namespaces tools from child MCPs to avoid conflicts
- Provides a single connection point for agents
- Maintains live links to mounted servers (tools added later are immediately visible)
- Zero duplication - no re-implementation of tools

## Architecture

The system uses **setuptools entrypoints** for plugin discovery:

```python
# In agent_toys_mcp/__init__.py
from agent_toys_mcp.discovery import get_mcp_servers

app = FastMCP("agent-toys-mcp")

# Automatically discover and mount all registered MCPs
for server in get_mcp_servers():
    app.mount(server)
```

## Features

### Automatic MCP Discovery

MCPs register themselves via entrypoints in their `pyproject.toml`:

```toml
[project.entry-points."agent_toys_mcp_mcp"]
mem-lite = "mem_lite_mcp.server:agent_toys_mcp_mcp"
```

When agent-toys-mcp loads, it automatically discovers all registered MCPs and mounts them.

### Memory Management Tools (from `mem-lite-mcp`)

All tools are automatically namespaced (when discovered):
- `mem_lite_save_memory` - Save new memory
- `mem_lite_update_memory` - Update existing memory
- `mem_lite_remove_memory` - Delete memory
- `mem_lite_search_memory` - Full-text search memories
- `mem_lite_get_memory` - Retrieve memory details
- `mem_lite_add_tag` - Add tags to memory
- `mem_lite_add_relation` - Link related memories

### Unified Prompts

- `mem_lite_maintenance` - Complete memory maintenance cycle

## Installation

### Minimal (without MCPs)

```bash
uv sync
```

This installs agent-toys-mcp without any MCPs. The app will load but warn about no plugins.

### Full (with all MCPs)

```bash
uv sync --all-groups
```

This installs all MCPs in the `full` dependency group.

## Running

```bash
# Via CLI (requires MCPs to be installed)
agent-toys-mcp

# Via Python module
python -m agent_toys_mcp

# Direct import and server.run()
uv run python -c "from agent_toys_mcp import app; app.run()"
```

## How Plugin Discovery Works

1. **MCP packages register** via `agent_toys_mcp_mcp` entrypoints:
   ```toml
   [project.entry-points."agent_toys_mcp_mcp"]
   my-mcp = "my_mcp.server:get_app"
   ```

2. **Entrypoint function returns** a FastMCP instance:
   ```python
   def agent_toys_mcp_mcp():
       return app  # FastMCP("my-mcp")
   ```

3. **agent-toys-mcp discovers and mounts** at startup:
   ```python
   from agent_toys_mcp.discovery import get_mcp_servers
   
   for server in get_mcp_servers():
       app.mount(server)  # Auto-namespaced
   ```

## Adding a New MCP

To create a new MCP compatible with agent-toys-mcp:

1. **Create the MCP package** (e.g., `packages/my-mcp/`)

2. **Define your FastMCP app** in `src/my_mcp/server.py`:
   ```python
   from fastmcp import FastMCP
   
   app = FastMCP("my-mcp")
   
   @app.tool()
   async def my_tool(param: str) -> str:
       return f"Hello {param}"
   
   # Register for agent-toys-mcp discovery
   def agent_toys_mcp_mcp():
       return app
   ```

3. **Register the entrypoint** in `pyproject.toml`:
   ```toml
   [project.entry-points."agent_toys_mcp_mcp"]
   my-mcp = "my_mcp.server:agent_toys_mcp_mcp"
   ```

4. **Add to agent-toys-mcp** (optional, for optional dependencies):
   
   Update `packages/agent-toys-mcp/pyproject.toml`:
   ```toml
   [tool.uv.sources]
   my-mcp = { workspace = true }
   
   [dependency-groups]
   full = [
       "mem-lite-mcp",
       "my-mcp",
   ]
   ```

5. **Sync workspace**:
   ```bash
   uv sync --all-groups
   ```

6. **Verify discovery**:
   ```bash
   uv run python -c "from agent_toys_mcp.discovery import get_mcp_servers; print(get_mcp_servers())"
   ```

That's it! No manual mounting needed.

## Testing

```bash
# Run discovery tests
uv run pytest packages/agent-toys-mcp/tests/test_discovery.py -v

# Test server composition
uv run python -c "from agent_toys_mcp import app; print(f'✓ {app.name} ready')"

# Test MCP discovery
uv run python << 'EOF'
from agent_toys_mcp.discovery import get_mcp_servers
servers = get_mcp_servers()
print(f"Discovered {len(servers)} MCP(s): {[s.name for s in servers]}")
EOF
```

## Discovery Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ agent-toys-mcp Startup                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
         ┌──────────────────────────────────────┐
         │ get_mcp_servers()                    │
         │ Scan setuptools entrypoints          │
         └──────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ↓               ↓               ↓
    ┌────────────────┐ ┌──────────────┐ ┌──────────────┐
    │ mem-lite-mcp   │ │ future-mcp   │ │ another-mcp  │
    │ (installed)    │ │ (installed)  │ │ (optional)   │
    └────────────────┘ └──────────────┘ └──────────────┘
            │               │               │
            └───────────────┼───────────────┘
                            ↓
         ┌──────────────────────────────────────┐
         │ FastMCP.mount() each server          │
         │ Automatic namespace isolation        │
         └──────────────────────────────────────┘
                            │
                            ↓
         ┌──────────────────────────────────────┐
         │ agent-toys-mcp ready with all tools      │
         │ mem_lite_*, future_*, another_*, ... │
         └──────────────────────────────────────┘
```

## Architecture

```
mem-lite/
├── packages/
│   ├── mem-lite-mcp/
│   │   ├── pyproject.toml (defines agent_toys_mcp_mcp entrypoint)
│   │   └── src/mem_lite_mcp/server.py (defines app + agent_toys_mcp_mcp())
│   └── agent-toys-mcp/
│       ├── pyproject.toml (minimal deps, optional dep groups)
│       ├── src/agent_toys_mcp/
│       │   ├── __init__.py (auto-mounts MCPs)
│       │   └── discovery.py (entrypoint scanning)
│       └── tests/
│           └── test_discovery.py (auto-discovery tests)
└── pyproject.toml (workspace)
```

## Dependencies

### Core (always required)

- `fastmcp>=3.4.2` - MCP server framework

### Optional (install with `--all-groups`)

- `mem-lite-mcp` - Memory management MCP (included in `full` group)

## Key Benefits

✅ **Automatic Discovery** - No manual registration needed
✅ **Plugin Architecture** - Add MCPs without modifying agent-toys-mcp
✅ **No Duplication** - Tools defined once, composed automatically
✅ **Namespace Isolation** - No conflicts between MCPs
✅ **Live Binding** - Tools added later are immediately visible
✅ **Optional Deps** - Install only what you need
✅ **Scalable** - Add MCPs to workspace without code changes
✅ **Maintainable** - Changes only in source MCPs

## Related

- See [FastMCP Composition](https://gofastmcp.com/servers/composition) for composition documentation
- See [packages/mem-lite-mcp/README.md](../mem-lite-mcp/README.md) for memory MCP details
- See [AGENTS.md](../../AGENTS.md) for workspace structure guidance
