"""SQLModel entities for Memory, Tag, and Relation with async support."""

from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, String
from ulid import ULID


def generate_ulid() -> str:
    """Generate a new ULID as string."""
    return str(ULID())


class Tag(SQLModel, table=True):
    """Represents a tag."""
    __tablename__ = "tags"
    
    id: str = Field(primary_key=True, max_length=26)
    name: str = Field(index=True)
    created_at: str


class MemoryBase(SQLModel):
    """Base memory model with common fields."""
    title: str
    content: str
    summary: Optional[str] = None
    tags_list: str = Field(default="")


class Memory(MemoryBase, table=True):
    """Represents a memory with auto-generated ULID."""
    __tablename__ = "memories"
    
    id: str = Field(primary_key=True, default_factory=generate_ulid, max_length=26)
    created_at: str
    last_read_at: str


class MemoryRead(MemoryBase):
    """Memory for reading (with ID and timestamps)."""
    id: str
    tags: List[str] = Field(default_factory=list)
    created_at: str
    last_read_at: str


class Relation(SQLModel, table=True):
    """Represents a relationship between two memories."""
    __tablename__ = "memory_relations"
    
    id: str = Field(primary_key=True, default_factory=generate_ulid, max_length=26)
    id_a: str = Field(index=True, max_length=26)
    id_b: str = Field(index=True, max_length=26)
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: str


class RelatedMemory(MemoryBase):
    """Related memory in search context."""
    id: str
    tags: List[str] = Field(default_factory=list)
    weight: float = 0.5
    distance: int = 1


class SearchResultItem(SQLModel):
    """Single search result item."""
    memory: MemoryRead
    fts5_score: float
    recency_score: float
    relation_score: float
    importance_score: float
    match_type: str = "direct_match"
    related: List[dict] = Field(default_factory=list)


class SearchResult(SQLModel):
    """Complete search result."""
    total_matches: int
    returned: int
    offset: int
    query_time_ms: float
    memories: List[dict] = Field(default_factory=list)
