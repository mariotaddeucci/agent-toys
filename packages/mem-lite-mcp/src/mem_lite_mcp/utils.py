"""Utility functions for ULID generation, tag normalization, and timestamp extraction."""

import re
from datetime import datetime
from ulid import ULID


def generate_ulid() -> str:
    """Generate a new ULID as string."""
    return str(ULID())


def ulid_to_timestamp(ulid_str: str) -> datetime:
    """Extract timestamp from a ULID."""
    try:
        ulid_obj = ULID.from_str(ulid_str)
        return ulid_obj.datetime()
    except Exception:
        return datetime.utcnow()


def normalize_tag(tag: str) -> str:
    """Normalize a tag to kebab-case.
    
    Converts to lowercase and replaces spaces/underscores with hyphens.
    Removes special characters.
    """
    # Convert to lowercase
    tag = tag.lower().strip()
    
    # Replace spaces and underscores with hyphens
    tag = re.sub(r'[\s_]+', '-', tag)
    
    # Remove special characters (keep only letters, numbers, hyphens)
    tag = re.sub(r'[^a-z0-9\-]', '', tag)
    
    # Remove duplicate hyphens
    tag = re.sub(r'-+', '-', tag)
    
    # Remove hyphens at edges
    tag = tag.strip('-')
    
    return tag


def get_now_timestamp() -> str:
    """Return current ISO 8601 timestamp."""
    return datetime.utcnow().isoformat() + 'Z'


def days_since(timestamp_str: str) -> float:
    """Calculate days since an ISO 8601 timestamp."""
    try:
        # Remove 'Z' if present
        ts_clean = timestamp_str.rstrip('Z')
        dt = datetime.fromisoformat(ts_clean)
        delta = datetime.utcnow() - dt
        return delta.total_seconds() / 86400  # seconds to days
    except Exception:
        return 0.0
