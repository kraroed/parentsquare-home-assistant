"""Polling coordinator and minimal notification persistence."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_FOLDER_ID,
    CONF_PRIVACY_MODE,
    DEFAULT_MAX_NOTIFICATIONS,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENDER_DOMAINS,
    DOMAIN,
    PRIVACY_METADATA,
)
from .models import NotificationRecord
from .processing import async_process_message
from .retention import prune_notifications

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .provider import EmailSource

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1


class ParentSquareCoordinator(DataUpdateCoordinator[tuple[NotificationRecord, ...]]):
    """Poll the selected mail folder and retain only minimal notification data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        source: EmailSource,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.entry = entry
        self.source = source
        self.folder_id = entry.options.get(CONF_FOLDER_ID, "inbox")
        self.privacy_mode = entry.data.get(CONF_PRIVACY_MODE, PRIVACY_METADATA)
        self._store = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}_{entry.entry_id}_notifications"
        )
        self._records: list[NotificationRecord] = []

    async def async_load_history(self) -> None:
        """Load body-free notification records from Home Assistant storage."""
        stored = await self._store.async_load()
        if not stored:
            return

        records: list[NotificationRecord] = []
        for item in stored.get("notifications", []):
            try:
                item = dict(item)
                item["received_at"] = datetime.fromisoformat(item["received_at"])
                records.append(NotificationRecord(**item))
            except (KeyError, TypeError, ValueError):
                _LOGGER.warning("Skipping an invalid stored ParentSquare record")
        self._records = prune_notifications(
            records,
            retention_days=DEFAULT_RETENTION_DAYS,
            max_records=DEFAULT_MAX_NOTIFICATIONS,
        )

    async def _async_update_data(self) -> tuple[NotificationRecord, ...]:
        """Fetch recent messages and update only changed or new records."""
        record_map = {
            record.deduplication_key: record for record in self._records
        }

        async for metadata in self.source.async_get_messages(
            self.folder_id, privacy_mode=self.privacy_mode
        ):
            stable_id = metadata.internet_message_id or metadata.message_id
            key = f"{metadata.provider_id}:{stable_id}"

            if key in record_map:
                # Read/unread status can change after the original notification.
                record_map[key] = replace(
                    record_map[key],
                    is_read=metadata.is_read,
                    subject=metadata.subject,
                    sender_address=metadata.sender_address,
                )
                continue

            record = await async_process_message(
                self.source,
                metadata,
                privacy_mode=self.privacy_mode,
                sender_domains=DEFAULT_SENDER_DOMAINS,
            )
            if record is not None:
                record_map[record.deduplication_key] = record

        self._records = prune_notifications(
            record_map.values(),
            retention_days=DEFAULT_RETENTION_DAYS,
            max_records=DEFAULT_MAX_NOTIFICATIONS,
        )
        await self._store.async_save(
            {"notifications": [self._serialize(record) for record in self._records]}
        )
        return tuple(self._records)

    @staticmethod
    def _serialize(record: NotificationRecord) -> dict[str, Any]:
        """Serialize a notification without any original message body."""
        serialized = asdict(record)
        serialized["received_at"] = record.received_at.isoformat()
        return serialized
