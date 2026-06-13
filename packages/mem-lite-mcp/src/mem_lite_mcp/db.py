"""Async SQLite database layer using SQLModel for memory management."""

from pathlib import Path
from typing import Optional, List, Tuple
from sqlmodel import SQLModel, create_engine, select, or_, and_, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from .models import Memory, MemoryRead, Tag, Relation, RelatedMemory, generate_ulid
from .utils import get_now_timestamp, normalize_tag


class Database:
    """Async SQLite database manager for memories using SQLModel."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize async database connection.
        
        Args:
            db_path: Database path. If None, uses ~/.mem-lite/memory.db
        """
        if db_path is None:
            db_path = Path.home() / ".mem-lite" / "memory.db"
        else:
            db_path = Path(db_path)
        
        # Create directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(db_path)
        self.db_url = f"sqlite+aiosqlite:///{self.db_path}"
        self.engine = None
        self.async_session = None
        self._initialized = False
    
    async def init_db(self):
        """Initialize database with async engine and create tables."""
        if self._initialized:
            return
        
        # Create async engine
        self.engine = create_async_engine(
            self.db_url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False}
        )
        
        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            
            # Enable foreign keys
            await conn.execute(text("PRAGMA foreign_keys = ON"))
        
        # Create session factory
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self._initialized = True
    
    async def get_session(self) -> AsyncSession:
        """Get async database session."""
        if not self._initialized:
            await self.init_db()
        return self.async_session()
    
    # ==================== MEMORIES ====================
    
    async def save_memory(self, memory_id: str, title: str, content: str, 
                         summary: Optional[str] = None, tags: List[str] = None) -> MemoryRead:
        """Save a new memory."""
        async with await self.get_session() as session:
            now = get_now_timestamp()
            tags = tags or []
            
            # Normalize tags
            normalized_tags = [normalize_tag(t) for t in tags]
            tags_list = " ".join(normalized_tags)
            
            # Create memory
            memory = Memory(
                id=memory_id,
                title=title,
                content=content,
                summary=summary,
                tags_list=tags_list,
                created_at=now,
                last_read_at=now
            )
            session.add(memory)
            
            # Create tags
            for tag_name in normalized_tags:
                tag_id = normalize_tag(tag_name)
                
                # Check if tag exists
                existing_tag = await session.execute(select(Tag).where(Tag.id == tag_id))
                existing_tag = existing_tag.scalar_one_or_none()
                
                if not existing_tag:
                    tag = Tag(id=tag_id, name=tag_name, created_at=now)
                    session.add(tag)
            
            await session.commit()
            await session.refresh(memory)
            
            return MemoryRead(
                id=memory.id,
                title=memory.title,
                content=memory.content,
                summary=memory.summary,
                tags=normalized_tags,
                tags_list=memory.tags_list,
                created_at=memory.created_at,
                last_read_at=memory.last_read_at
            )
    
    async def get_memory_by_id(self, memory_id: str) -> Optional[MemoryRead]:
        """Get a memory by ID."""
        async with await self.get_session() as session:
            memory = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = memory.scalar_one_or_none()
            
            if not memory:
                return None
            
            # Fetch tags
            tags = []
            if memory.tags_list:
                tags = memory.tags_list.split()
            
            return MemoryRead(
                id=memory.id,
                title=memory.title,
                content=memory.content,
                summary=memory.summary,
                tags=tags,
                tags_list=memory.tags_list,
                created_at=memory.created_at,
                last_read_at=memory.last_read_at
            )
    
    async def get_memories_by_ids(self, memory_ids: List[str]) -> List[MemoryRead]:
        """Get multiple memories by IDs."""
        memories = []
        for mem_id in memory_ids:
            mem = await self.get_memory_by_id(mem_id)
            if mem:
                memories.append(mem)
        return memories
    
    async def update_memory(self, memory_id: str, title: Optional[str] = None,
                           content: Optional[str] = None, summary: Optional[str] = None) -> bool:
        """Update a memory (only title/content/summary)."""
        async with await self.get_session() as session:
            memory = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = memory.scalar_one_or_none()
            
            if not memory:
                return False
            
            if title is not None:
                memory.title = title
            if content is not None:
                memory.content = content
            if summary is not None:
                memory.summary = summary
            
            session.add(memory)
            await session.commit()
            return True
    
    async def delete_memory(self, memory_id: str) -> dict:
        """Delete a memory (with CASCADE cleanup)."""
        async with await self.get_session() as session:
            # Count relations that will be deleted
            relations = await session.execute(
                select(func.count(Relation.id)).where(
                    or_(Relation.id_a == memory_id, Relation.id_b == memory_id)
                )
            )
            relations_removed = relations.scalar() or 0
            
            # Delete memory
            memory = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = memory.scalar_one_or_none()
            
            if memory:
                await session.delete(memory)
                await session.commit()
            
            return {
                "tags_removed": 0,
                "relations_removed": relations_removed
            }
    
    async def update_last_read(self, memory_ids: List[str]):
        """Update last_read_at for multiple memories."""
        if not memory_ids:
            return
        
        async with await self.get_session() as session:
            now = get_now_timestamp()
            memories = await session.execute(
                select(Memory).where(Memory.id.in_(memory_ids))
            )
            memories = memories.scalars().all()
            
            for memory in memories:
                memory.last_read_at = now
                session.add(memory)
            
            await session.commit()
    
    # ==================== TAGS ====================
    
    async def add_tag_to_memory(self, memory_id: str, tag_name: str) -> Tuple[str, str]:
        """Add a tag to a memory."""
        tag_id = normalize_tag(tag_name)
        async with await self.get_session() as session:
            now = get_now_timestamp()
            
            # Get memory
            memory = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = memory.scalar_one_or_none()
            
            if not memory:
                raise ValueError(f"Memory not found: {memory_id}")
            
            # Create tag if it doesn't exist
            tag = await session.execute(select(Tag).where(Tag.id == tag_id))
            tag = tag.scalar_one_or_none()
            
            if not tag:
                tag = Tag(id=tag_id, name=tag_name, created_at=now)
                session.add(tag)
            
            # Update tags_list
            if tag_id not in memory.tags_list.split():
                memory.tags_list = " ".join(sorted(set(memory.tags_list.split()) | {tag_id}))
                session.add(memory)
            
            await session.commit()
            return tag_id, now
    
    # ==================== RELATIONS ====================
    
    async def add_relation(self, memory_id_1: str, memory_id_2: str, weight: float = 0.5) -> Relation:
        """Add a relationship between two memories (bidirectional)."""
        # Normalize IDs: id_a = min, id_b = max
        id_a, id_b = sorted([memory_id_1, memory_id_2])
        
        # No self-loops
        if id_a == id_b:
            raise ValueError("Cannot create relation with the same memory")
        
        async with await self.get_session() as session:
            relation_id = generate_ulid()
            now = get_now_timestamp()
            
            # Check if relation exists
            existing = await session.execute(
                select(Relation).where(
                    and_(Relation.id_a == id_a, Relation.id_b == id_b)
                )
            )
            existing = existing.scalar_one_or_none()
            
            if existing:
                existing.weight = weight
                session.add(existing)
            else:
                relation = Relation(
                    id=relation_id,
                    id_a=id_a,
                    id_b=id_b,
                    weight=weight,
                    created_at=now
                )
                session.add(relation)
            
            await session.commit()
            
            return Relation(
                id=relation_id,
                id_a=id_a,
                id_b=id_b,
                weight=weight,
                created_at=now
            )
    
    async def get_related_memories(self, memory_id: str, depth: int = 1) -> List[dict]:
        """Get related memories (returns list of dicts with memory data)."""
        async with await self.get_session() as session:
            related = []
            
            # Depth 1: direct relations
            relations = await session.execute(
                select(Relation).where(
                    or_(Relation.id_a == memory_id, Relation.id_b == memory_id)
                )
            )
            relations = relations.scalars().all()
            
            for rel in relations:
                other_id = rel.id_b if rel.id_a == memory_id else rel.id_a
                mem = await self.get_memory_by_id(other_id)
                
                if mem:
                    related.append({
                        "other_id": mem.id,
                        "weight": rel.weight,
                        "distance": 1
                    })
            
            # Depth 2: indirect relations (if depth > 1)
            if depth > 1:
                direct_ids = {r["other_id"] for r in related}
                
                if direct_ids:
                    # Find relations connected to direct relations
                    indirect_relations = await session.execute(
                        select(Relation).where(
                            or_(
                                Relation.id_a.in_(direct_ids),
                                Relation.id_b.in_(direct_ids)
                            )
                        )
                    )
                    indirect_relations = indirect_relations.scalars().all()
                    
                    for rel in indirect_relations:
                        other_id = rel.id_b if rel.id_a in direct_ids else rel.id_a
                        
                        # Skip if already in depth 1 or is the original memory
                        if other_id not in direct_ids and other_id != memory_id:
                            mem = await self.get_memory_by_id(other_id)
                            if mem:
                                related.append({
                                    "other_id": mem.id,
                                    "weight": rel.weight,
                                    "distance": 2
                                })
            
            return related
