"""Sensors for ParentSquare email notifications."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ParentSquareCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up ParentSquare notification sensors."""
    coordinator: ParentSquareCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    async_add_entities(
        [
            ParentSquareUnreadSensor(coordinator, entry),
            ParentSquareLatestSensor(coordinator, entry),
        ]
    )


class ParentSquareBaseSensor(
    CoordinatorEntity[ParentSquareCoordinator], SensorEntity
):
    """Base sensor for the ParentSquare mailbox."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: ParentSquareCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ParentSquare email notifications",
            manufacturer="ParentSquare email integration",
            model="Microsoft Graph mailbox",
        )


class ParentSquareUnreadSensor(ParentSquareBaseSensor):
    """Count unread notifications in the retained recent window."""

    _attr_name = "Unread notifications"
    _attr_icon = "mdi:email-alert"

    def __init__(
        self, coordinator: ParentSquareCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_unread"

    @property
    def native_value(self) -> int:
        """Return the unread count in the retained notification window."""
        return sum(
            record.is_read is False for record in self.coordinator.data or ()
        )

    @property
    def extra_state_attributes(self) -> dict[str, int | str]:
        """Explain the bounded count window."""
        return {
            "count_scope": "retained recent notifications",
            "records_tracked": len(self.coordinator.data or ()),
        }


class ParentSquareLatestSensor(ParentSquareBaseSensor):
    """Expose the latest notification subject and concise summary."""

    _attr_name = "Latest notification"
    _attr_icon = "mdi:email-outline"

    def __init__(
        self, coordinator: ParentSquareCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_latest"

    @property
    def native_value(self) -> str | None:
        """Return the latest message subject."""
        records = self.coordinator.data or ()
        return records[0].subject if records else None

    @property
    def extra_state_attributes(self) -> dict[str, str | bool | None]:
        """Return minimal metadata and the optional short summary."""
        records = self.coordinator.data or ()
        if not records:
            return {}
        latest = records[0]
        return {
            "summary": latest.summary,
            "sender": latest.sender_address,
            "received_at": latest.received_at.isoformat(),
            "child_id": latest.child_id,
            "is_read": latest.is_read,
        }
