# AGENTS.md

## Setup
- Install: `uv sync --all-groups`
- Python: 3.11+
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
- Line length: 120
- Quote style: Double quotes
- Type checking: Pyrefly (Rust-based, faster than Pyright)
- Linting: Ruff (27 rules: quality, security, performance)
- **Pythonic and pragmatic**: follow the Zen of Python — explicit over implicit, simple over complex, flat over nested, readability counts
- No unnecessary abstractions; solve the problem at hand, not hypothetical future ones

## FastMCP Conventions
- **Logger**: always use `mcp.get_logger(__name__)` — never `logging.getLogger` or `print`
- **Lifespan**: use `@asynccontextmanager` lifespan on the FastMCP app for startup/teardown (DB init, connections, cleanup) — not ad-hoc module-level init
- **Tools**: all tools are `async def`; must `await` all I/O and DB calls
- **Resources**: prefer FastMCP resources (`@mcp.resource`) for read-only data access over custom tools when the data is addressable by URI
- **Prompts**: use `@mcp.prompt` for reusable prompt templates — keep tools focused on actions
- Example lifespan pattern:
  ```python
  from contextlib import asynccontextmanager
  from fastmcp import FastMCP

  mcp = FastMCP("my-server")
  logger = mcp.get_logger(__name__)

  @asynccontextmanager
  async def lifespan(app):
      logger.info("Starting up")
      await init_db()
      yield
      logger.info("Shutting down")

  mcp = FastMCP("my-server", lifespan=lifespan)
  ```

## Testing
- **Use plain functions**, not classes — `def test_something():` not `class TestSomething`
- Group related tests by module/file, not by class hierarchy
- Use `pytest.fixture` for shared setup; prefer function-scoped fixtures
- Use `anyio` or `pytest-anyio` for async tests (`@pytest.mark.anyio`)
- Test behavior, not implementation; avoid mocking internals — mock at system boundaries
- One assertion concept per test; name tests to read as sentences: `test_save_memory_returns_id`

## Architecture
- **mem-lite-mcp**: Memory management (7 async tools, SQLModel + SQLite)
- **agent-toys-mcp**: Auto-discovering MCP aggregator (FastMCP composition)
- **Discovery**: Entrypoint-based plugin system (no hard-coded imports)
- **Tests**: 70 total (59 mem-lite + 11 agent-toys)

## Adding a New MCP Package
1. Create `packages/your-mcp/src/your_mcp/server.py` with FastMCP app + lifespan
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
- Memory DB path: `~/.mem-lite/memory.db` (auto-created)
- Field validation happens at MCP protocol layer, not direct calls
- Each package has nested AGENTS.md with detailed guidance
