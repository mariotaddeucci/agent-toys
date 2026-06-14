# AGENTS.md

## Setup
- Install: `uv sync --all-groups`
- Python: 3.14+
- Lock file: Always commit `uv.lock`

## Build & Test
- Run tests: `uv run pytest tests/ -v`
- Run single test: `uv run pytest tests/test_consolidation.py::test_consolidated_app_loads -v`

## Code Style
- Language: English only
- Line length: 100
- Quote style: Double quotes
- All code is async/await (where applicable)

## Architecture
- **Entry point**: `agent_toys_mcp:main()` → `app.run()` (FastMCP)
- **Zero hard-coded imports**: Uses entrypoint-based plugin discovery
- **FastMCP composition**: Mounts all discovered MCPs automatically
- **Tests**: 11 async test functions (consolidation, discovery)

## Discovery Mechanism
1. On startup, scans for entrypoints in `agent_toys_mcp` group
2. Loads each entrypoint function
3. Calls function to get FastMCP instance
4. Mounts each instance to main app
5. Ready for client connections

## Key Commands
- Check if app loads:
  ```bash
  uv run python -c "from agent_toys_mcp import app; print(app.name)"
  ```

- List discovered MCPs:
  ```bash
  uv run python -c "from agent_toys_mcp.discovery import get_mcp_servers; print(get_mcp_servers())"
  ```

- Run the server:
  ```bash
  uv run agent-toys-mcp
  ```

## Adding a New MCP
1. Create `packages/your-mcp/src/your_mcp/server.py`:
   ```python
   from fastmcp import FastMCP

   app = FastMCP("your-mcp")

   @app.tool()
   async def your_tool(param: str) -> str:
       return f"Result: {param}"

   def agent_toys_mcp_mcp():
       return app
   ```

2. Register in `packages/your-mcp/pyproject.toml`:
   ```toml
   [project.entry-points."agent_toys_mcp"]
   your-mcp = "your_mcp.server:agent_toys_mcp_mcp"
   ```

3. Sync workspace: `uv sync --all-groups`

4. Verify: `uv run python -c "from agent_toys_mcp.discovery import get_mcp_servers; print(get_mcp_servers())"`

## File Structure
```
src/agent_toys_mcp/
├── __init__.py           # Entry point: main()
├── server.py             # FastMCP app (no tools)
└── discovery.py          # Entrypoint scanning + loading
```

## Common Issues
1. **MCP not discovered**: Check entrypoint name is exactly `agent_toys_mcp`
2. **Function not returning FastMCP**: Return value must be FastMCP instance
3. **Tools not visible**: Run `uv sync --all-groups` to install MCPs
4. **Import errors**: Verify entrypoint path matches actual module structure
