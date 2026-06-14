# Agent Instructions for mem-lite Workspace

## Language Convention

**All code, documentation, comments, and commit messages must be in English.** This includes:
- Source code and variable names
- Documentation files (README.md, AGENTS.md, etc.)
- Docstrings and inline comments
- Commit messages
- Code review comments

This ensures consistency and accessibility across the entire workspace.

---

## Workspace Architecture

### High-Level Overview

```
mem-lite (uv workspace)
│
├── mem-lite-mcp              # Memory management MCP
│   ├── 7 async tools (FastMCP)
│   ├── SQLModel ORM + SQLite
│   └── Registers via entrypoint: agent_toys_mcp
│
└── agent-toys-mcp            # Auto-discovering MCP aggregator
    ├── Minimal core (fastmcp only)
    ├── Auto-discovers MCPs via setuptools entrypoints
    ├── Mounts all discovered MCPs
    └── Exposes unified interface to clients
```

### Key Design Principles

1. **Plugin Architecture**: MCPs register themselves via entrypoints, not hard-coded imports
2. **Zero Duplication**: Each tool defined once, composed at runtime
3. **Minimal Core**: agent-toys-mcp has zero dependencies on specific MCPs
4. **Namespace Isolation**: FastMCP composition automatically namespaces tools
5. **Live Binding**: Tools added to child MCPs are immediately visible
6. **Optional Dependencies**: Install only what you need via dependency groups

### Discovery Mechanism

```
Startup Sequence:
1. agent-toys-mcp imports
2. _load_mcp_plugins() called
3. get_mcp_servers() scans "agent_toys_mcp" entrypoints
4. Loads all registered MCP functions
5. Mounts each FastMCP instance
6. Ready for client connections
```

---

## Important: CLAUDE.md Symlinks

Each package directory contains a **symlink** to `~/.claude/CLAUDE.md`:

```
packages/mem-lite-mcp/CLAUDE.md -> ../../../.claude/CLAUDE.md
packages/agent-toys-mcp/CLAUDE.md -> ../../../.claude/CLAUDE.md
```

**When creating new packages**, always create a similar symlink:

```bash
ln -sf ../../../.claude/CLAUDE.md packages/your-new-mcp/CLAUDE.md
```

This ensures consistent agent instructions across the workspace without duplication.

---

## Workspace Structure

This is a `uv` workspace with two FastMCP packages using **auto-discovery via setuptools entrypoints**:

- **`mem-lite-mcp`**: Memory management MCP server (7 async tools, SQLModel + SQLite)
- **`agent-toys-mcp`**: Auto-discovering MCP aggregator using FastMCP composition + entrypoint plugins

**Python**: 3.14+ | **Build**: `uv` | **Lock file**: `uv.lock`

For detailed guidance, see `packages/mem-lite-mcp/AGENTS.md` and `packages/agent-toys-mcp/README.md`

---

## Essential Commands

### Setup & Run

```bash
# Minimal (agent-toys-mcp only, no MCPs)
uv sync

# Full (with all MCPs in 'full' dependency group)
uv sync --all-groups

# Run servers
uv run agent-toys-mcp

uv run mem-lite-mcp

# Run tests
uv run pytest
```

### Verify Workspace Health

```bash
# Check sync status
uv sync --check

# Verify agent-toys-mcp loads (no MCPs required)
uv run python -c "from agent_toys_mcp import app; print(f'✓ {app.name}')"

# Check discovered MCPs (if full group installed)
uv run python -c "from agent_toys_mcp.discovery import get_mcp_servers; print(f'Discovered: {[s.name for s in get_mcp_servers()]}')"

# Verify mem-lite-mcp directly
uv run python -c "from mem_lite_mcp.server import app; print(f'✓ {app.name}')"
```

---

## Workspace Rules & Patterns

### Package Boundaries

- **mem-lite-mcp**: Defines `app` (FastMCP server) + 7 memory tools
  - Entry: `mem_lite_mcp.server:app` 
  - Plugin entry: `mem_lite_mcp.server:agent_toys_mcp_mcp` (for discovery)
  - Registered in `pyproject.toml` under `[project.entry-points."agent_toys_mcp_mcp"]`

- **agent-toys-mcp**: Auto-discovers and mounts child MCPs
  - Entry: `agent_toys_mcp:app` (exported from `__init__.py`)
  - Uses setuptools entrypoint discovery (no hard imports)
  - FastMCP composition (zero tool re-implementation)

### Adding a New MCP Package (NEW: Entrypoint-Based)

The new **autodiscovery system** means you don't modify agent-toys-mcp to add a new MCP:

1. **Create** `packages/your-mcp/` with `src/your_mcp/server.py`:
   ```python
   from fastmcp import FastMCP
   
   app = FastMCP("your-mcp")
   
   @app.tool()
   async def your_tool(param: str) -> str:
       return f"Result: {param}"
   
   # Register for agent-toys-mcp discovery
   def agent_toys_mcp_mcp():
       return app
   ```

2. **Register entrypoint** in `packages/your-mcp/pyproject.toml`:
   ```toml
   [project.entry-points."agent_toys_mcp_mcp"]
   your-mcp = "your_mcp.server:agent_toys_mcp_mcp"
   ```

3. **(Optional) Add to workspace** in root `pyproject.toml`:
   ```toml
   [tool.uv.workspace]
   members = [
       "packages/mem-lite-mcp",
       "packages/agent-toys-mcp",
       "packages/your-mcp",  # Add here
   ]
   ```

4. **(Optional) Add to optional deps** in `packages/agent-toys-mcp/pyproject.toml`:
   ```toml
   [tool.uv.sources]
   your-mcp = { workspace = true }
   
   [dependency-groups]
   full = [
       "mem-lite-mcp",
       "your-mcp",  # Add here
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

**That's it!** agent-toys-mcp will automatically discover and mount your MCP at startup.

### How Autodiscovery Works

```
agent-toys-mcp startup:
1. Call get_mcp_servers() from discovery.py
2. Scan for all entrypoints in "agent_toys_mcp_mcp" group
3. Load each entrypoint function
4. Call function to get FastMCP instance
5. Mount each instance to app
```

**Advantages over manual mounting:**
- ✅ No code changes to agent-toys-mcp needed
- ✅ MCPs register themselves via entrypoints
- ✅ Scalable - add MCPs to workspace without touching aggregator
- ✅ Works with optional dependencies

### Workspace Dependency Updates

- **Core packages** use `[tool.uv.sources]` to reference each other (see agent-toys-mcp)
- **agent-toys-mcp** has minimal core deps, optional MCPs in `full` group
- **Changes** to mem-lite-mcp are immediately visible after `uv sync`
- Always commit `uv.lock` after dependency changes

---

## Common Gotchas

1. **Forgot to sync after changing dependencies**  
   → Run `uv sync --all-groups`

2. **MCP not discovered**  
   → Verify entrypoint exists in `pyproject.toml`: `[project.entry-points."agent_toys_mcp_mcp"]`
   → Check function is named `agent_toys_mcp_mcp()` and returns FastMCP instance
   → List entrypoints: `python -m importlib.metadata` (or check in code)

3. **Tools not appearing in agent-toys-mcp**  
   → Install full group: `uv sync --all-groups`
   → Check: `uv run python -c "from agent_toys_mcp.discovery import get_mcp_servers; print(get_mcp_servers())"`

4. **Tests fail in workspace context**  
   → Run from workspace root: `uv run pytest`

5. **agent-toys-mcp runs but warns about no MCPs**  
   → This is normal if you didn't install the `full` group
   → Install with: `uv sync --all-groups`

---

## File Reference

```
mem-lite/
├── pyproject.toml                     # Workspace root: members list
├── uv.lock                            # Lock file (commit this)
├── README.md                          # Workspace overview
├── AGENTS.md                          # ← You are here
├── packages/
│   ├── mem-lite-mcp/
│   │   ├── pyproject.toml             # Defines agent_toys_mcp_mcp entrypoint
│   │   ├── AGENTS.md                  # Detailed memory tool guidance
│   │   ├── README.md
│   │   ├── src/mem_lite_mcp/
│   │   │   ├── __init__.py            # Entry point: calls main()
│   │   │   ├── __main__.py            # CLI: mem-lite-mcp
│   │   │   ├── server.py              # 7 tools + 1 prompt + agent_toys_mcp_mcp()
│   │   │   ├── tools.py               # MemoryTools impl
│   │   │   ├── db.py                  # AsyncDatabase
│   │   │   ├── models.py              # SQLModel definitions
│   │   │   └── utils.py               # ULID, tag normalization
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── test_memory_crud.py
│   │       ├── test_search.py
│   │       ├── test_tags_relations.py
│   │       └── test_integration_and_edge_cases.py
│   └── agent-toys-mcp/
│       ├── pyproject.toml             # Minimal deps + optional full group
│       ├── README.md                  # Plugin architecture docs
│       ├── src/agent_toys_mcp/
│       │   ├── __init__.py            # Auto-mounts MCPs via discovery
│       │   └── discovery.py           # Entrypoint scanning + loading
│       └── tests/
│           └── test_discovery.py      # Auto-discovery tests
```

---

## Next Session Context

- **Preserve** existing package `AGENTS.md` files; root file is workspace-level
- **When adding MCP**: Register entrypoint, optionally add to workspace + optional deps, `uv sync --all-groups`
- **Keep** `uv.lock` committed; don't manually edit
- **Run tests** from workspace root: `uv run pytest` (discovers all packages)
- **Discovery** uses setuptools entrypoints: `[project.entry-points."agent_toys_mcp_mcp"]` group

4. **Async operation without await**  
   → All tools are `async def`; must `await` calls

5. **Import path confusion**  
   → Use `from mem_lite_mcp.server import app`, not relative imports

---

## When to Check Package-Specific Guidance

- **Modifying mem-lite-mcp tools, schema, validation, or tests**  
  → Read `packages/mem-lite-mcp/AGENTS.md`

- **Adding a new tool to mem-lite-mcp**  
  → 1. Implement async method in `tools.py`  
  → 2. Register with `@app.tool()` in `server.py` with Field validation  
  → 3. Update README tool table  
  → 4. Add tests to `tests/`  
  → 5. Run `uv run pytest`

- **Changing agent-toys-mcp composition**  
  → Edit `packages/agent-toys-mcp/src/agent_toys_mcp/__init__.py`  
  → Verify with: `uv run python -c "from agent_toys_mcp import app; print(app.tools)"`

---

## File Reference

```
mem-lite/
├── pyproject.toml                     # Workspace root: members list
├── uv.lock                            # Lock file (commit this)
├── README.md                          # Workspace overview
├── AGENTS.md                          # ← You are here
├── packages/
│   ├── mem-lite-mcp/
│   │   ├── CLAUDE.md                  # → Symlink to ~/.claude/CLAUDE.md
│   │   ├── pyproject.toml             # Defines agent_toys_mcp entrypoint
│   │   ├── AGENTS.md                  # Detailed memory tool guidance
│   │   ├── README.md
│   │   ├── src/mem_lite_mcp/
│   │   │   ├── __init__.py            # Entry point: calls main()
│   │   │   ├── __main__.py            # CLI: mem-lite-mcp
│   │   │   ├── server.py              # 7 tools + 1 prompt + agent_toys_mcp()
│   │   │   ├── tools.py               # MemoryTools impl
│   │   │   ├── db.py                  # AsyncDatabase
│   │   │   ├── models.py              # SQLModel definitions
│   │   │   └── utils.py               # ULID, tag normalization
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── test_memory_crud.py
│   │       ├── test_search.py
│   │       ├── test_tags_relations.py
│   │       └── test_integration_and_edge_cases.py
│   └── agent-toys-mcp/
│       ├── CLAUDE.md                  # → Symlink to ~/.claude/CLAUDE.md
│       ├── pyproject.toml             # Minimal deps + optional full group
│       ├── README.md                  # Plugin architecture docs
│       ├── src/agent_toys_mcp/
│       │   ├── __init__.py            # Auto-mounts MCPs via discovery
│       │   └── discovery.py           # Entrypoint scanning + loading
│       └── tests/
│           └── test_discovery.py      # Auto-discovery tests
```

---

## Next Session Context

- **Preserve** existing package `AGENTS.md` files; root file is workspace-level
- **When creating new packages**, always create a symlink: `ln -sf ../../../.claude/CLAUDE.md packages/your-new-mcp/CLAUDE.md`
- **When adding MCP**: Register entrypoint, optionally add to workspace + optional deps, `uv sync --all-groups`
- **Keep** `uv.lock` committed; don't manually edit
- **Run tests** from workspace root: `uv run pytest` (discovers all packages)
- **Discovery** uses setuptools entrypoints: `[project.entry-points."agent_toys_mcp"]` group
