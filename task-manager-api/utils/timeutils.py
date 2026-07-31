from datetime import datetime, timezone


def utc_now():
    """Substitui datetime.utcnow() (deprecated) mantendo datetime naive UTC p/ SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
