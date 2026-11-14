"""ParentSquare email notification integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .const import DOMAIN
from .microsoft_graph import MicrosoftGraphEmailSource

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration domain."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up an authenticated Microsoft mailbox connection."""
    from homeassistant.const import Platform
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from homeassistant.helpers.config_entry_oauth2_flow import (
        OAuth2Session,
        async_get_config_entry_implementation,
    )

    from .coordinator import ParentSquareCoordinator

    implementation = await async_get_config_entry_implementation(hass, entry)
    oauth_session = OAuth2Session(hass, entry, implementation)
    await oauth_session.async_ensure_token_valid()

    source = MicrosoftGraphEmailSource(
        oauth_session, async_get_clientsession(hass)
    )
    coordinator = ParentSquareCoordinator(hass, entry, source)
    await coordinator.async_load_history()
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "oauth_session": oauth_session,
        "source": source,
        "coordinator": coordinator,
    }
    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform.SENSOR]
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload the Microsoft mailbox connection."""
    from homeassistant.const import Platform

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform.SENSOR]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
