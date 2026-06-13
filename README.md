# mem-lite

A lightweight MCP (Model Context Protocol) server for memory management using SQLite with full-text search, ULID generation, bidirectional relational graph system, and async/await architecture with comprehensive Field validation.

## Features

- **Async Architecture**: 100% non-blocking operations with async/await and aiosqlite
- **SQLModel Integration**: Automatic table creation with type-safe ORM
- **ULID-based IDs**: Automatically generated ULIDs for memories with embedded timestamps
- **Full-Text Search**: FTS5 indexed search across title, content, summary, and tags
- **Intelligent Scoring**: Importance scoring combines FTS5 relevance (40%), recency (30%), and relationship density (30%)
- **Bidirectional Relations**: Create relationships between memories that work in both directions
- **Normalized Tags**: All tags automatically normalized to kebab-case
- **Bulk Operations**: Get multiple memories in a single tool call
- **Cascade Delete**: Automatic cleanup of related records when a memory is deleted
- **Field Validation**: Comprehensive input validation with Pydantic Field metadata
- **SQLite Backend**: Persistent storage in `~/.mem-lite/memory.db`

## Installation

### Prerequisites
- Python 3.14+
- `uv` package manager

### Setup

```bash
git clone <repo>
cd mem-lite
uv sync
```

## Database Schema

```sql
memories
├─ id (ULID, primary key)
├─ title, content, summary
├─ tags_list (denormalized for FTS5)
├─ created_at (extracted from ULID)
└─ last_read_at (auto-updated on search/get)

tags
├─ id (kebab-case)
└─ name

memory_tags (junction table)
├─ memory_id (FK→memories)
└─ tag_id (FK→tags)

memory_relations (bidirectional graph)
├─ id (ULID)
├─ id_a, id_b (normalized: min, max)
└─ weight (0-1)
```

## 7 Tools (All with Field Validation)

All tools follow FastMCP best practices with comprehensive Pydantic Field validation, descriptions, and constraints for LLM clients.

### 1. `save_memory`

Creates a new memory with automatic ULID generation.

**Parameters:**
- `title` (str): Memory title (min: 1, max: 500 chars) **required**
- `content` (str): Full memory content (min: 1, max: 50,000 chars) **required**
- `summary` (str): Optional memory summary (max: 1,000 chars) **optional**
- `tags` (list[str]): Tags (auto-normalized to kebab-case) **optional**

**Example:**
```json
{
  "title": "Python Basics",
  "content": "Full content here...",
  "summary": "Optional summary",
  "tags": ["python", "tutorial"]
}
```

**Output:**
```json
{
  "memory_id": "01KV1KMJV6G5TS8A...",
  "created_at": "2026-06-13T10:30:45.123Z",
  "title": "Python Basics",
  "tags_added": ["python", "tutorial"]
}
```

### 2. `update_memory`

Updates title, content, or summary of an existing memory.

**Parameters:**
- `memory_id` (str): Memory ID (26-char ULID, pattern: `^[0-9A-Z]{26}$`) **required**
- `title` (str): New title (min: 1, max: 500) **optional**
- `content` (str): New content (min: 1, max: 50,000) **optional**
- `summary` (str): New summary (max: 1,000) **optional**

**Example:**
```json
{
  "memory_id": "01KV1KMJV6G5TS8A",
  "title": "New Title",
  "content": "Updated content..."
}
```

**Output:**
```json
{
  "memory_id": "01KV1KMJV6G5TS8A",
  "updated_fields": ["title", "content"]
}
```

### 3. `remove_memory`

Hard delete a memory with automatic CASCADE cleanup.

**Parameters:**
- `memory_id` (str): Memory ID (26-char ULID) **required**

**Example:**
```json
{
  "memory_id": "01KV1KMJV6G5TS8A"
}
```

**Output:**
```json
{
  "memory_id": "01KV1KMJV6G5TS8A",
  "deleted": true,
  "cascade_deleted": {
    "tags_removed": 3,
    "relations_removed": 2
  }
}
```

### 4. `search_memory` (Super Tool)

Full-text search with importance scoring and related memories up to depth 2.

**Parameters:**
- `query` (str): Search term(s) (min: 1, max: 200) **required**
- `tags_filter` (list[str]): Tags to filter (AND logic) **optional**
- `depth` (int): Related memory depth (1-2, default: 1) **optional**
- `limit` (int): Max results (1-100, default: 20) **optional**
- `offset` (int): Pagination offset (≥ 0, default: 0) **optional**
- `max_memories_per_result` (int): Max returned (1-20, default: 5) **optional**
- `max_relations_per_memory` (int): Max relations (1-10, default: 5) **optional**

**Example:**
```json
{
  "query": "API",
  "tags_filter": ["python"],
  "depth": 2,
  "limit": 20,
  "offset": 0
}
```

**Output:**
```json
{
  "total_matches": 5,
  "returned": 2,
  "offset": 0,
  "query_time_ms": 12.34,
  "memories": [
    {
      "memory": {
        "id": "01KV1KMJV6G5TS8A",
        "title": "FastAPI Tutorial",
        "summary": "Quick start...",
        "tags": ["fastapi", "python"],
        "created_at": "2026-06-13T10:30:45Z",
        "last_read_at": "2026-06-13T12:45:00Z"
      },
      "fts5_score": 0.95,
      "recency_score": 0.95,
      "relation_score": 0.08,
      "importance_score": 0.771,
      "match_type": "direct_match",
      "related": [
        {
          "id": "01KV1KMJV8HW2QH4",
          "weight": 0.9,
          "distance": 1
        }
      ]
    }
  ]
}
```

### 5. `get_memory`

Retrieve multiple memories with complete content.

**Parameters:**
- `memory_ids` (list[str]): Memory IDs to retrieve (min: 1, max: 50) **required**

**Example:**
```json
{
  "memory_ids": ["01KV1KMJV6G5TS8A", "01KV1KMJV8HW2QH4"]
}
```

**Output:**
```json
{
  "memories": [
    {
      "id": "01KV1KMJV6G5TS8A",
      "title": "FastAPI Tutorial",
      "content": "Full content here...",
      "summary": "Quick start...",
      "tags": ["fastapi", "python"],
      "created_at": "2026-06-13T10:30:45Z",
      "last_read_at": "2026-06-13T12:45:00Z"
    }
  ],
  "count": 1
}
```

### 6. `add_tag`

Add a tag to a memory (auto-normalized to kebab-case).

**Parameters:**
- `memory_id` (str): Memory ID (26-char ULID) **required**
- `tag_name` (str): Tag name (min: 1, max: 100) **required**

**Example:**
```json
{
  "memory_id": "01KV1KMJV6G5TS8A",
  "tag_name": "Best Practices"
}
```

**Output:**
```json
{
  "tag_id": "best-practices",
  "memory_id": "01KV1KMJV6G5TS8A",
  "tag_name": "best-practices",
  "created_at": "2026-06-13T10:45:00Z"
}
```

### 7. `add_relation`

Create a bidirectional relationship between two memories.

**Parameters:**
- `memory_id_1` (str): First memory ID (26-char ULID) **required**
- `memory_id_2` (str): Second memory ID (26-char ULID) **required**
- `weight` (float): Relationship strength (0.0-1.0, default: 0.5) **optional**

**Example:**
```json
{
  "memory_id_1": "01KV1KMJV6G5TS8A",
  "memory_id_2": "01KV1KMJV8HW2QH4",
  "weight": 0.8
}
```

**Output:**
```json
{
  "relation_id": "01KV1KMJV9Z1X2Y3",
  "id_a": "01KV1KMJV6G5TS8A",
  "id_b": "01KV1KMJV8HW2QH4",
  "weight": 0.8,
  "created_at": "2026-06-13T10:50:00Z",
  "bidirectional": true
}
```

## Scoring Algorithm

The `search_memory` tool returns an `importance_score` (0-1) combining three factors:

```
importance_score = (FTS5_score * 0.5) + (Recency_score * 0.3) + (Relations_score * 0.2)

Where:
  - FTS5_score: Normalized BM25 relevance from full-text search
  - Recency_score: 1 / (1 + days_since_last_read / 7)  [meia-vida ~7 days]
  - Relations_score: (direct_relations + indirect_relations * 0.5) / 100
```

This ensures recently accessed, well-connected memories rank higher even with lower text relevance.

## Scoring Algorithm

The `search_memory` tool returns an `importance_score` (0-1) combining three factors:

```
importance_score = (FTS5_score * 0.4) + (Recency_score * 0.3) + (Relations_score * 0.3)

Where:
  - FTS5_score: Full-text search relevance ranking
  - Recency_score: Time since last read (higher = more recent)
  - Relations_score: Normalized count of direct/indirect relations
```

This ensures recently accessed, well-connected memories rank higher even with lower text relevance.

## File Structure

```
src/mem_lite/
├─ __init__.py        # FastMCP entry point
├─ server.py          # Tool registration with @mcp.tool() and Field validation
├─ tools.py           # Implementation of 7 async tools
├─ db.py              # Async SQLite database layer with SQLModel
├─ models.py          # SQLModel definitions (Memory, Tag, Relation, etc)
└─ utils.py           # ULID, kebab-case, timestamp helpers
```

## Database Location

All memories are stored in `~/.mem-lite/memory.db` and automatically created on first run.

## Testing

Run the comprehensive test suite:

```bash
uv run python -c "
import tempfile
from pathlib import Path
from mem_lite.tools import MemoryTools

# Full integration test with all 7 tools
db_path = Path(tempfile.mkdtemp()) / 'test.db'
tools = MemoryTools(str(db_path))

# ... test code ...
"
```

## Architecture Highlights

- **Async/Await**: 100% non-blocking operations with aiosqlite and AsyncSession
- **SQLModel ORM**: Automatic table creation and type-safe database operations
- **Field Validation**: Comprehensive Pydantic Field constraints:
  - String length limits (min/max_length)
  - Numeric ranges (ge/le for greater/less than)
  - Regex patterns for ULID validation (26-char alphanumeric)
  - Collection size constraints (min_items/max_items)
  - Human-readable descriptions for LLM clients
- **No Manual Schema Management**: SQLModel.metadata.create_all() handles migrations
- **FTS5 Indexing**: Efficient full-text search with BM25 ranking
- **Cascade Deletes**: PRAGMA foreign_keys enabled for automatic cleanup
- **Denormalized Tags**: Tags stored in `tags_list` field for better FTS5 performance
- **Lazy Tool Initialization**: Tools only created when first accessed
- **Timestamp Extraction**: ULIDs contain embedded timestamps

## MCP Integration

This project is a FastMCP server ready for integration with Claude or other MCP clients.

Run the server:

```bash
uv run mem-lite
```

Or import directly in Python:

```python
from mem_lite.server import app
# Use with your MCP client
```

## License

MIT
