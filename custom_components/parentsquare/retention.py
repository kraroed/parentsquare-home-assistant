"""Bounded notification retention helpers."""

from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from .models import NotificationRecord


def prune_notifications(
    records: Iterable[NotificationRecord],
    *,
    now: datetime | None = None,
    retention_days: int = 30,
    max_records: int = 250,
) -> list[NotificationRecord]:
    """Keep only recent records, newest first, within a hard item limit."""
    current = now or datetime.now(timezone.utc)
    cutoff = current - timedelta(days=max(0, retention_days))
    retained = [record for record in records if record.received_at >= cutoff]
    retained.sort(key=lambda record: record.received_at, reverse=True)
    return retained[: max(0, max_records)]
