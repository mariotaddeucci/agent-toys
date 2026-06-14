
from sqlmodel import Field, SQLModel
from ulid import ULID


def generate_ulid() -> str:
    return str(ULID())


class Tag(SQLModel, table=True):
    __tablename__ = "tags"

    id: str = Field(primary_key=True, max_length=26)
    name: str = Field(index=True)
    created_at: str


class MemoryBase(SQLModel):
    title: str
    content: str
    summary: str | None = None
    tags_list: str = Field(default="")


class Memory(MemoryBase, table=True):
    __tablename__ = "memories"

    id: str = Field(primary_key=True, default_factory=generate_ulid, max_length=26)
    created_at: str
    last_read_at: str


class MemoryRead(MemoryBase):
    id: str
    tags: list[str] = Field(default_factory=list)
    created_at: str
    last_read_at: str


class Relation(SQLModel, table=True):
    __tablename__ = "memory_relations"

    id: str = Field(primary_key=True, default_factory=generate_ulid, max_length=26)
    id_a: str = Field(index=True, max_length=26)
    id_b: str = Field(index=True, max_length=26)
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: str


class RelatedMemory(MemoryBase):
    id: str
    tags: list[str] = Field(default_factory=list)
    weight: float = 0.5
    distance: int = 1


class SearchResultItem(SQLModel):
    memory: MemoryRead
    fts5_score: float
    recency_score: float
    relation_score: float
    importance_score: float
    match_type: str = "direct_match"
    related: list[dict] = Field(default_factory=list)


class SearchResult(SQLModel):
    total_matches: int
    returned: int
    offset: int
    query_time_ms: float
    memories: list[dict] = Field(default_factory=list)
