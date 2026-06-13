# mem-lite

Memory management system using FastMCP, SQLite, and async/await architecture.

## Workspace Structure

This is a `uv` workspace containing the following packages:

### `packages/mem-lite-mcp`

FastMCP server for memory management with:
- **7 async tools** for memory CRUD, search, tags, and relations
- **SQLModel ORM** with SQLite backend
- **Pydantic Field validation** at MCP protocol layer
- **FastMCP dependency injection** using `Depends()`
- **1 comprehensive maintenance prompt** for knowledge base cleanup
- **59 async test functions** across 4 test modules

See [packages/mem-lite-mcp/README.md](packages/mem-lite-mcp/README.md) for detailed documentation.

### `packages/agent-toys`

Consolidated MCP aggregator that combines all workspace MCPs into a single unified connection point:
- Imports and re-exports all tools from workspace MCPs
- Provides unified namespace with prefixed tools (e.g., `mem_*` for mem-lite)
- Combines all prompts under single connection
- Single entry point for multi-MCP agents

See [packages/agent-toys/README.md](packages/agent-toys/README.md) for detailed documentation.

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests for mem-lite-mcp
cd packages/mem-lite-mcp && uv run pytest

# Run the consolidated agent-toys server
uv run agent-toys

# Or run mem-lite directly
uv run mem-lite-mcp
```

## Workspace Commands

```bash
# Sync all packages
uv sync

# Run tests for specific package
cd packages/mem-lite-mcp && uv run pytest

# Run tests for agent-toys
cd packages/agent-toys && uv run pytest

# Test consolidated server
uv run python -c "from agent_toys import app; print(f'✓ {app.name} ready')"
```

## Structure

```
mem-lite/
├── pyproject.toml              # Workspace root configuration
├── README.md                   # This file
├── .python-version
├── uv.lock                     # Lock file for reproducible builds
└── packages/
    ├── mem-lite-mcp/           # Memory management MCP
    │   ├── pyproject.toml
    │   ├── README.md
    │   ├── AGENTS.md
    │   ├── src/mem_lite_mcp/
    │   │   ├── __init__.py
    │   │   ├── __main__.py
    │   │   ├── server.py (7 tools + prompts)
    │   │   ├── tools.py
    │   │   ├── db.py
    │   │   ├── models.py
    │   │   └── utils.py
    │   └── tests/ (59 tests)
    └── agent-toys/             # Consolidated MCP aggregator
        ├── pyproject.toml
        ├── README.md
        ├── src/agent_toys/
        │   ├── __init__.py (imports & re-exports mem-lite tools)
        │   └── __main__.py
        └── tests/
```

## Entry Points

### mem-lite-mcp
- **CLI**: `mem-lite-mcp` → runs memory MCP server alone
- **Module**: `python -m mem_lite_mcp` → same as above

### agent-toys
- **CLI**: `agent-toys` → runs consolidated aggregator
- **Module**: `python -m agent_toys` → same as above

## Architecture

**agent-toys** consolidates MCPs by:
1. Importing individual MCP apps (`mem_lite_mcp.server.app`)
2. Re-registering tools with prefixed names (`mem_save_memory`, etc.)
3. Re-registering prompts with prefixed names (`mem_maintenance`, etc.)
4. Providing single FastMCP app that routes to all MCPs

This allows agents to connect once and access tools from multiple MCPs.

## Development

All packages use:
- `fastmcp>=3.4.2` - MCP server framework
- `sqlmodel>=0.0.14` - SQLModel ORM (mem-lite-mcp)
- `python-ulid>=2.3.0` - ULID generation (mem-lite-mcp)
- `uv` - Package and workspace management

See individual package READMEs for detailed development guides.

## Adding New MCPs

To add a new MCP to the workspace:

1. Create package structure: `packages/your-mcp/`
2. Define tools and prompts in `src/your_mcp/server.py`
3. Add to workspace: `pyproject.toml` → `[tool.uv.workspace].members`
4. Import in `agent-toys` and re-export with prefixes
5. Sync workspace: `uv sync`

## Features

- ✅ Async-only architecture with SQLite/async ORM
- ✅ FastMCP dependency injection with `Depends()`
- ✅ Pydantic Field validation on all tools
- ✅ Comprehensive test coverage (59 tests for mem-lite)
- ✅ Single consolidated connection point
- ✅ Extensible workspace for multiple MCPs

