# AGENTS.md

## Setup
- Install: `uv sync`
- Python: 3.14+
- Database: `~/.mem-lite/memory.db` (auto-created)

## Build & Test
- Run tests: `uv run pytest tests/ -v`
- Run single test: `uv run pytest tests/test_memory_crud.py::test_save_memory_basic -v`

## Code Style
- Language: English only
- Line length: 100
- Quote style: Double quotes
- All code is async/await (no sync operations)

## Architecture
- **Entry point**: `mem_lite_mcp:main()` → `app.run()` (FastMCP)
- **7 Tools**: save_memory, update_memory, remove_memory, search_memory, get_memory, add_tag, add_relation
- **Database**: SQLModel ORM + SQLite + aiosqlite
- **Tests**: 59 async test functions (CRUD, search, tags, relations, edge cases)

## Key Commands
- Test a single tool:
  ```python
  import asyncio
  from mem_lite_mcp.tools import MemoryTools
  
  async def test():
      tools = MemoryTools(":memory:")
      result = await tools.save_memory("title", "content")
      print(result)
  
  asyncio.run(test())
  ```

- Verify all tools work:
  ```bash
  uv run python -c "from mem_lite_mcp.server import app; print(f'✓ {app.name}')"
  ```

## Common Gotchas
1. **ULID Format**: Always 26 characters, alphanumeric uppercase `[0-9A-Z]{26}`
2. **Tag Normalization**: "Machine Learning" → "machine-learning"
3. **Async/Await Required**: Every DB operation must be awaited
4. **Field Validation**: Constraints enforced only at MCP protocol layer, not direct calls
5. **Default DB Path**: `MemoryTools()` with no args → `~/.mem-lite/memory.db`

## File Structure
```
src/mem_lite_mcp/
├── __init__.py           # Entry point: main()
├── server.py             # 7 async @mcp.tool() functions
├── tools.py              # MemoryTools class implementation
├── db.py                 # AsyncDatabase + SQLModel
├── models.py             # Memory, Tag, Relation definitions
└── utils.py              # Helpers: ULID, timestamps, tag normalization
```
