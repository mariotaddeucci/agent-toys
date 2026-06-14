from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, and_, func, or_, select

from mem_lite_mcp.models import Memory, MemoryRead, Relation, Tag, generate_ulid
from mem_lite_mcp.utils import get_now_timestamp, normalize_tag


class Database:

    def __init__(self, db_path: str | Path | None = None) -> None:
        db_path = Path.home() / ".mem-lite" / "memory.db" if db_path is None else Path(db_path)

        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = str(db_path)
        self.db_url = f"sqlite+aiosqlite:///{self.db_path}"
        self.engine = None
        self.async_session = None
        self._initialized = False

    async def init_db(self):
        if self._initialized:
            return

        self.engine = create_async_engine(
            self.db_url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False}
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            await conn.execute(text("PRAGMA foreign_keys = ON"))

        self.async_session = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        self._initialized = True

    async def get_session(self) -> AsyncSession:
        if not self._initialized:
            await self.init_db()
        return self.async_session()

    async def save_memory(self, memory_id: str, title: str, content: str,
                         summary: str | None = None, tags: list[str] | None = None) -> MemoryRead:
        async with await self.get_session() as session:
            now = get_now_timestamp()
            tags = tags or []

            normalized_tags = [normalize_tag(t) for t in tags]
            tags_list = " ".join(normalized_tags)

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

            for tag_name in normalized_tags:
                tag_id = normalize_tag(tag_name)

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

    async def get_memory_by_id(self, memory_id: str) -> MemoryRead | None:
        async with await self.get_session() as session:
            memory = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = memory.scalar_one_or_none()

            if not memory:
                return None

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

    async def get_memories_by_ids(self, memory_ids: list[str]) -> list[MemoryRead]:
        memories = []
        for mem_id in memory_ids:
            mem = await self.get_memory_by_id(mem_id)
            if mem:
                memories.append(mem)
        return memories

    async def update_memory(self, memory_id: str, title: str | None = None,
                           content: str | None = None, summary: str | None = None) -> bool:
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
        async with await self.get_session() as session:
            relations = await session.execute(
                select(func.count(Relation.id)).where(
                    or_(Relation.id_a == memory_id, Relation.id_b == memory_id)
                )
            )
            relations_removed = relations.scalar() or 0

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

    async def update_last_read(self, memory_ids: list[str]):
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

    async def add_tag_to_memory(self, memory_id: str, tag_name: str) -> tuple[str, str]:
        tag_id = normalize_tag(tag_name)
        async with await self.get_session() as session:
            now = get_now_timestamp()

            memory = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = memory.scalar_one_or_none()

            if not memory:
                msg = f"Memory not found: {memory_id}"
                raise ValueError(msg)

            tag = await session.execute(select(Tag).where(Tag.id == tag_id))
            tag = tag.scalar_one_or_none()

            if not tag:
                tag = Tag(id=tag_id, name=tag_name, created_at=now)
                session.add(tag)

            if tag_id not in memory.tags_list.split():
                memory.tags_list = " ".join(sorted(set(memory.tags_list.split()) | {tag_id}))
                session.add(memory)

            await session.commit()
            return tag_id, now

    async def add_relation(self, memory_id_1: str, memory_id_2: str, weight: float = 0.5) -> Relation:
        id_a, id_b = sorted([memory_id_1, memory_id_2])

        if id_a == id_b:
            msg = "Cannot create relation with the same memory"
            raise ValueError(msg)

        async with await self.get_session() as session:
            relation_id = generate_ulid()
            now = get_now_timestamp()

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

    async def get_related_memories(self, memory_id: str, depth: int = 1) -> list[dict]:
        async with await self.get_session() as session:
            related = []

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

            if depth > 1:
                direct_ids = {r["other_id"] for r in related}

                if direct_ids:
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

                        if other_id not in direct_ids and other_id != memory_id:
                            mem = await self.get_memory_by_id(other_id)
                            if mem:
                                related.append({
                                    "other_id": mem.id,
                                    "weight": rel.weight,
                                    "distance": 2
                                })

            return related
