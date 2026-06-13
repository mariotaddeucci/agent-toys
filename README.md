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

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest packages/mem-lite-mcp/tests -v

# Run the MCP server
uv run mem-lite-mcp
```

## Workspace Commands

```bash
# Sync all packages
uv sync

# Run tests for specific package
cd packages/mem-lite-mcp && uv run pytest

# Install package in development mode
uv pip install -e packages/mem-lite-mcp
```

## Structure

```
mem-lite/
├── pyproject.toml              # Workspace root configuration
├── README.md                   # This file
├── .python-version
├── uv.lock                     # Lock file for reproducible builds
└── packages/
    └── mem-lite-mcp/           # FastMCP server package
        ├── pyproject.toml
        ├── README.md
        ├── AGENTS.md
        ├── src/
        │   └── mem_lite_mcp/   # Main module
        │       ├── __init__.py
        │       ├── __main__.py
        │       ├── server.py
        │       ├── tools.py
        │       ├── db.py
        │       ├── models.py
        │       └── utils.py
        └── tests/
            ├── conftest.py
            ├── test_memory_crud.py
            ├── test_search.py
            ├── test_tags_relations.py
            └── test_integration_and_edge_cases.py
```

## Entry Points

- **CLI**: `mem-lite-mcp` → runs the FastMCP server
- **Module**: `python -m mem_lite_mcp` → same as above

## Development

All development work happens in `packages/mem-lite-mcp`. See its README for:
- Architecture details
- Tool specifications
- Testing guide
- Development workflows
