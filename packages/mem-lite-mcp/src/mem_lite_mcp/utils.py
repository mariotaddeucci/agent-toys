import re
from datetime import datetime
from ulid import ULID


def generate_ulid() -> str:
    return str(ULID())


def ulid_to_timestamp(ulid_str: str) -> datetime:
    try:
        ulid_obj = ULID.from_str(ulid_str)
        return ulid_obj.datetime()
    except Exception:
        return datetime.utcnow()


def normalize_tag(tag: str) -> str:
    tag = tag.lower().strip()
    tag = re.sub(r'[\s_]+', '-', tag)
    tag = re.sub(r'[^a-z0-9\-]', '', tag)
    tag = re.sub(r'-+', '-', tag)
    tag = tag.strip('-')
    return tag


def get_now_timestamp() -> str:
    return datetime.utcnow().isoformat() + 'Z'


def days_since(timestamp_str: str) -> float:
    try:
        ts_clean = timestamp_str.rstrip('Z')
        dt = datetime.fromisoformat(ts_clean)
        delta = datetime.utcnow() - dt
        return delta.total_seconds() / 86400
    except Exception:
        return 0.0
