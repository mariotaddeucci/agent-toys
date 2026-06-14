import time
from typing import Any

from mem_lite_mcp.db import Database
from mem_lite_mcp.models import MemoryRead
from mem_lite_mcp.utils import generate_ulid, normalize_tag


class MemoryTools:

    def __init__(self, db_path: str | None = None) -> None:
        self.db = Database(db_path)

    async def save_memory(self, title: str, content: str, summary: str | None = None,
                         tags: list[str] | None = None) -> dict[str, Any]:
        await self.db.init_db()
        memory_id = generate_ulid()
        tags = tags or []

        memory = await self.db.save_memory(memory_id, title, content, summary, tags)

        return {
            "memory_id": memory.id,
            "created_at": memory.created_at,
            "title": memory.title,
            "tags_added": memory.tags
        }

    async def update_memory(self, memory_id: str, title: str | None = None,
                           content: str | None = None,
                           summary: str | None = None) -> dict[str, Any]:
        updated = await self.db.update_memory(memory_id, title, content, summary)

        if not updated:
            msg = f"Memory not found: {memory_id}"
            raise ValueError(msg)

        updated_fields = []
        if title is not None:
            updated_fields.append("title")
        if content is not None:
            updated_fields.append("content")
        if summary is not None:
            updated_fields.append("summary")

        return {
            "memory_id": memory_id,
            "updated_fields": updated_fields
        }

    async def remove_memory(self, memory_id: str) -> dict[str, Any]:
        cascade_stats = await self.db.delete_memory(memory_id)

        return {
            "memory_id": memory_id,
            "deleted": True,
            "cascade_deleted": cascade_stats
        }

    async def search_memory(self, query: str, tags_filter: list[str] | None = None,
                           depth: int = 1, limit: int = 20, offset: int = 0,
                           max_memories_per_result: int = 5,
                           max_relations_per_memory: int = 5) -> dict[str, Any]:
        start_time = time.time()

        tags_filter = [normalize_tag(t) for t in (tags_filter or [])]

        async with await self.db.get_session() as session:
            from sqlmodel import func, or_, select

            from mem_lite_mcp.models import Memory

            query_lower = f"%{query.lower()}%"

            stmt = select(Memory).where(
                or_(
                    Memory.title.ilike(query_lower),
                    Memory.content.ilike(query_lower),
                    Memory.summary.ilike(query_lower) if Memory.summary is not None else False
                )
            )

            if tags_filter:
                for tag in tags_filter:
                    stmt = stmt.where(Memory.tags_list.contains(tag))

            count_stmt = select(func.count(Memory.id)).select_from(Memory).where(
                or_(
                    Memory.title.ilike(query_lower),
                    Memory.content.ilike(query_lower),
                    Memory.summary.ilike(query_lower) if Memory.summary is not None else False
                )
            )

            if tags_filter:
                for tag in tags_filter:
                    count_stmt = count_stmt.where(Memory.tags_list.contains(tag))

            total_result = await session.execute(count_stmt)
            total_matches = total_result.scalar() or 0

            stmt = stmt.offset(offset).limit(limit)

            result = await session.execute(stmt)
            memories = result.scalars().all()

        result_items = []
        for memory in memories:
            memory_read = MemoryRead(
                id=memory.id,
                title=memory.title,
                content=memory.content,
                summary=memory.summary,
                tags=memory.tags_list.split() if memory.tags_list else [],
                tags_list=memory.tags_list,
                created_at=memory.created_at,
                last_read_at=memory.last_read_at
            )

            related = await self.db.get_related_memories(memory.id, depth=depth)
            related = related[:max_relations_per_memory]

            fts5_score = 1.0 if query.lower() in memory.title.lower() else 0.7
            recency_score = 0.8
            relation_score = min(len(related) / 5.0, 1.0)
            importance_score = (fts5_score * 0.4 + recency_score * 0.3 + relation_score * 0.3)

            item = {
                "memory": {
                    "id": memory_read.id,
                    "title": memory_read.title,
                    "summary": memory_read.summary,
                    "tags": memory_read.tags,
                    "created_at": memory_read.created_at,
                    "last_read_at": memory_read.last_read_at
                },
                "fts5_score": round(fts5_score, 2),
                "recency_score": round(recency_score, 2),
                "relation_score": round(relation_score, 2),
                "importance_score": round(importance_score, 2),
                "match_type": "direct_match",
                "related": [
                    {
                        "id": r['other_id'],
                        "weight": round(r['weight'], 2),
                        "distance": r['distance']
                    }
                    for r in related
                ]
            }
            result_items.append(item)

        result_items = result_items[:max_memories_per_result]

        if result_items:
            memory_ids = [item["memory"]["id"] for item in result_items]
            await self.db.update_last_read(memory_ids)

        query_time = (time.time() - start_time) * 1000

        return {
            "total_matches": total_matches,
            "returned": len(result_items),
            "offset": offset,
            "query_time_ms": round(query_time, 2),
            "memories": result_items
        }

    async def get_memory(self, memory_ids: list[str]) -> dict[str, Any]:
        memories = await self.db.get_memories_by_ids(memory_ids)

        found_ids = [m.id for m in memories]
        await self.db.update_last_read(found_ids)

        return {
            "memories": [
                {
                    "id": m.id,
                    "title": m.title,
                    "content": m.content,
                    "summary": m.summary,
                    "tags": m.tags,
                    "created_at": m.created_at,
                    "last_read_at": m.last_read_at
                }
                for m in memories
            ],
            "count": len(memories)
        }

    async def add_tag(self, memory_id: str, tag_name: str) -> dict[str, Any]:
        tag_id, created_at = await self.db.add_tag_to_memory(memory_id, tag_name)

        return {
            "tag_id": tag_id,
            "memory_id": memory_id,
            "tag_name": tag_id,
            "created_at": created_at
        }

    async def add_relation(self, memory_id_1: str, memory_id_2: str,
                          weight: float = 0.5) -> dict[str, Any]:
        if weight < 0 or weight > 1:
            msg = "Weight must be between 0 and 1"
            raise ValueError(msg)

        relation = await self.db.add_relation(memory_id_1, memory_id_2, weight)

        return {
            "relation_id": relation.id,
            "id_a": relation.id_a,
            "id_b": relation.id_b,
            "weight": relation.weight,
            "created_at": relation.created_at,
            "bidirectional": True
        }
