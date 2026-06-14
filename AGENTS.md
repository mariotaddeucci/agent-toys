# AGENTS.md

## Setup
- Install: `uv sync --all-groups`
- Python: 3.14+
- Lock file: Always commit `uv.lock`

## Build & Test
- Run linter: `uv run ruff check packages/`
- Run formatter: `uv run ruff format packages/`
- Run type checker: `uv run pyrefly check packages/`
- Run tests: `cd packages/mem-lite-mcp && uv run pytest tests/ -v`
- Run agent tests: `cd packages/agent-toys-mcp && uv run pytest tests/ -v`
- Full validation: `uv run ruff check packages/ && uv run pyrefly check packages/ && cd packages/mem-lite-mcp && uv run pytest tests/ && cd ../agent-toys-mcp && uv run pytest tests/`

## Code Style
- Language: **English only** (code, docs, comments, commits)
- Line length: 100
- Quote style: Double quotes
- Type checking: Pyrefly (Rust-based, faster than Pyright)
- Linting: Ruff (27 rules: quality, security, performance)

## Architecture
- **mem-lite-mcp**: Memory management (7 async tools, SQLModel + SQLite)
- **agent-toys-mcp**: Auto-discovering MCP aggregator (FastMCP composition)
- **Discovery**: Entrypoint-based plugin system (no hard-coded imports)
- **Tests**: 70 total (59 mem-lite + 11 agent-toys)

## Adding a New MCP Package
1. Create `packages/your-mcp/src/your_mcp/server.py` with FastMCP app
2. Register entrypoint in `[project.entry-points."agent_toys_mcp"]` (pyproject.toml)
3. Add to workspace members list if needed
4. Run `uv sync --all-groups`

## Key Commands
- Verify app loads: `uv run python -c "from agent_toys_mcp import app; print(app.name)"`
- Check discovered MCPs: `uv run python -c "from agent_toys_mcp.discovery import get_mcp_servers; print(get_mcp_servers())"`
- Run MCP server: `uv run agent-toys-mcp` or `uv run mem-lite-mcp`

## Validators
- **Ruff** (v0.5.0+): Linting + formatting (27 rules)
- **Pyrefly** (v1.0.0+): Type checking (Rust-based)
- **Pytest**: Unit tests (70 tests)

## Notes
- All tools are `async def`; must `await` all DB calls
- Memory DB path: `~/.mem-lite/memory.db` (auto-created)
- Field validation happens at MCP protocol layer, not direct calls
- Each package has nested AGENTS.md with detailed guidance
