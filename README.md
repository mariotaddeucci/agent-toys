# mem-lite

A lightweight MCP (Model Context Protocol) server for memory management using SQLite with full-text search (FTS5), ULID generation, and a bidirectional relational graph system.

## Features

- **ULID-based IDs**: Automatically generated ULIDs for memories with embedded timestamps
- **Full-Text Search**: FTS5 indexed search across title, content, summary, and tags
- **Intelligent Scoring**: Importance scoring combines FTS5 relevance (50%), recency (30%), and relationship density (20%)
- **Bidirectional Relations**: Create relationships between memories that work in both directions
- **Normalized Tags**: All tags automatically normalized to kebab-case
- **Bulk Operations**: Get multiple memories in a single tool call
- **Cascade Delete**: Automatic cleanup of related records when a memory is deleted
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

## 7 Tools

### 1. `save_memory`

Creates a new memory with automatic ULID generation.

**Input:**
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

Updates title, content, or summary of an existing memory (tags managed separately).

**Input:**
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

Hard delete a memory with automatic CASCADE cleanup of tags and relations.

**Input:**
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

Full-text search with importance scoring and related memories. Returns both direct matches and semantically related memories up to 2 levels deep.

**Input:**
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
      "fts5_score": 25.3,
      "recency_score": 0.95,
      "relation_score": 0.08,
      "importance_score": 0.771,
      "match_type": "direct_match",
      "related": [
        {
          "id": "01KV1KMJV8HW2QH4",
          "title": "REST API Design",
          "summary": "API best practices...",
          "tags": ["api", "rest"],
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

**Input:**
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

Add a tag to a memory (tags auto-normalized to kebab-case).

**Input:**
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

**Input:**
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

## File Structure

```
src/mem_lite/
├─ __init__.py        # FastMCP entry point
├─ server.py          # Tool registration with FastMCP
├─ tools.py           # Implementation of 7 tools
├─ db.py              # SQLite database layer
├─ models.py          # Dataclasses (Memory, Tag, Relation, etc)
├─ utils.py           # ULID, kebab-case, timestamp helpers
├─ scoring.py         # Importance scoring algorithm
└─ schema.sql         # SQLite DDL
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

- **No External Dependencies for Storage**: Pure SQLite, no ORM overhead
- **FTS5 Indexing**: Efficient full-text search with BM25 ranking
- **Cascade Deletes**: PRAGMA foreign_keys enabled for automatic cleanup
- **Denormalized Tags**: Tags stored in `tags_list` field for better FTS5 performance
- **Lazy Tool Initialization**: Tools only created when first accessed
- **Timestamp Extraction**: ULIDs contain embedded timestamps, no separate field needed

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
