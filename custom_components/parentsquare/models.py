"""Provider-neutral data models.

These models intentionally contain no Home Assistant or provider SDK dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

PrivacyMode = Literal["metadata", "summary"]


@dataclass(frozen=True, slots=True)
class EmailMessageMetadata:
    """Minimal message metadata returned by an email provider."""

    provider_id: str
    message_id: str
    sender_address: str
    subject: str
    received_at: datetime
    sender_name: str | None = None
    internet_message_id: str | None = None
    folder_id: str | None = None
    is_read: bool | None = None


@dataclass(frozen=True, slots=True)
class ChildMatchRule:
    """An explicit user-defined set of terms used to associate a message."""

    child_id: str
    terms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NotificationRecord:
    """Persistable notification data; never contains the original email body."""

    deduplication_key: str
    provider_id: str
    message_id: str
    sender_address: str
    subject: str
    received_at: datetime
    summary: str
    child_id: str | None = None
    is_read: bool | None = None
