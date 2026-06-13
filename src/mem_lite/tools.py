"""Implementation of the 7 tools for the MCP Server."""

import time
from typing import List, Optional, Dict, Any
from .db import Database
from .models import Memory, MemoryRead, SearchResultItem, SearchResult, RelatedMemory
from .utils import generate_ulid, normalize_tag


class MemoryTools:
    """Set of tools for managing memories."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db = Database(db_path)
    
    # ==================== 1. SAVE_MEMORY ====================
    
    async def save_memory(self, title: str, content: str, summary: Optional[str] = None,
                         tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Save a new memory with auto-generated ULID.
        
        Args:
            title: Memory title
            content: Full content
            summary: Optional summary
            tags: List of tags (will be normalized to kebab-case)
        
        Returns:
            Dict with memory_id, created_at, title, tags_added
        """
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
    
    # ==================== 2. UPDATE_MEMORY ====================
    
    async def update_memory(self, memory_id: str, title: Optional[str] = None,
                           content: Optional[str] = None, 
                           summary: Optional[str] = None) -> Dict[str, Any]:
        """Update title/content/summary of a memory.
        
        Args:
            memory_id: Memory ID to update
            title: New title (optional)
            content: New content (optional)
            summary: New summary (optional)
        
        Returns:
            Dict with memory_id and updated_fields
        """
        updated = await self.db.update_memory(memory_id, title, content, summary)
        
        if not updated:
            raise ValueError(f"Memory not found: {memory_id}")
        
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
    
    # ==================== 3. REMOVE_MEMORY ====================
    
    async def remove_memory(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory (hard delete with CASCADE cleanup).
        
        Args:
            memory_id: ID of memory to delete
        
        Returns:
            Dict with memory_id, deleted status, and cascade_deleted counts
        """
        cascade_stats = await self.db.delete_memory(memory_id)
        
        return {
            "memory_id": memory_id,
            "deleted": True,
            "cascade_deleted": cascade_stats
        }
    
    # ==================== 4. SEARCH_MEMORY ====================
    
    async def search_memory(self, query: str, tags_filter: Optional[List[str]] = None,
                           depth: int = 1, limit: int = 20, offset: int = 0,
                           max_memories_per_result: int = 5,
                           max_relations_per_memory: int = 5) -> Dict[str, Any]:
        """Search memories with full-text search + related memories + importance scoring.
        
        Args:
            query: Search term
            tags_filter: Tags to filter (AND logic)
            depth: Depth of relations (1 or 2)
            limit: Maximum number of results (default 20)
            offset: Offset for pagination (default 0)
            max_memories_per_result: Maximum memories to return (default 5)
            max_relations_per_memory: Maximum related memories per result (default 5)
        
        Returns:
            Dict with total_matches, returned, memories with scores and related
        """
        start_time = time.time()
        
        # Normalize tags
        tags_filter = [normalize_tag(t) for t in (tags_filter or [])]
        
        # Get all memories (simple search for now - can be improved with FTS5 later)
        async with await self.db.get_session() as session:
            from sqlmodel import select, or_, func
            from .models import Memory
            
            # Search in title, content, and summary
            query_lower = f"%{query.lower()}%"
            
            stmt = select(Memory).where(
                or_(
                    Memory.title.ilike(query_lower),
                    Memory.content.ilike(query_lower),
                    Memory.summary.ilike(query_lower) if Memory.summary is not None else False
                )
            )
            
            # Apply tag filters if provided
            if tags_filter:
                # Filter by tags_list containing all tags
                for tag in tags_filter:
                    stmt = stmt.where(Memory.tags_list.contains(tag))
            
            # Count total
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
            
            # Apply pagination
            stmt = stmt.offset(offset).limit(limit)
            
            result = await session.execute(stmt)
            memories = result.scalars().all()
        
        # Process results with scoring
        result_items = []
        for memory in memories:
            # Convert to MemoryRead
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
            
            # Get related memories
            related = await self.db.get_related_memories(memory.id, depth=depth)
            related = related[:max_relations_per_memory]
            
            # Calculate simple scores
            fts5_score = 1.0 if query.lower() in memory.title.lower() else 0.7
            recency_score = 0.8  # Simplified for now
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
        
        # Apply memory limit
        result_items = result_items[:max_memories_per_result]
        
        # Update last_read_at for returned memories
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
    
    # ==================== 5. GET_MEMORY ====================
    
    async def get_memory(self, memory_ids: List[str]) -> Dict[str, Any]:
        """Get multiple memories with complete content.
        
        Args:
            memory_ids: List of memory IDs
        
        Returns:
            Dict with memories (complete content) and count
        """
        memories = await self.db.get_memories_by_ids(memory_ids)
        
        # Update last_read_at
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
    
    # ==================== 6. ADD_TAG ====================
    
    async def add_tag(self, memory_id: str, tag_name: str) -> Dict[str, Any]:
        """Add a tag to a memory.
        
        Args:
            memory_id: Memory ID
            tag_name: Tag name (will be normalized)
        
        Returns:
            Dict with tag_id, memory_id, created_at
        """
        tag_id, created_at = await self.db.add_tag_to_memory(memory_id, tag_name)
        
        return {
            "tag_id": tag_id,
            "memory_id": memory_id,
            "tag_name": tag_id,
            "created_at": created_at
        }
    
    # ==================== 7. ADD_RELATION ====================
    
    async def add_relation(self, memory_id_1: str, memory_id_2: str,
                          weight: float = 0.5) -> Dict[str, Any]:
        """Add bidirectional relationship between two memories.
        
        Args:
            memory_id_1: First ID
            memory_id_2: Second ID
            weight: Relationship weight (0-1, default 0.5)
        
        Returns:
            Dict with relation_id, id_a, id_b, weight, created_at
        """
        if weight < 0 or weight > 1:
            raise ValueError("Weight must be between 0 and 1")
        
        relation = await self.db.add_relation(memory_id_1, memory_id_2, weight)
        
        return {
            "relation_id": relation.id,
            "id_a": relation.id_a,
            "id_b": relation.id_b,
            "weight": relation.weight,
            "created_at": relation.created_at,
            "bidirectional": True
        }
