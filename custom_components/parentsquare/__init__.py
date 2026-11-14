"""ParentSquare email notification integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)

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
    implementation = await async_get_config_entry_implementation(hass, entry)
    oauth_session = OAuth2Session(hass, entry, implementation)
    await oauth_session.async_ensure_token_valid()

    source = MicrosoftGraphEmailSource(
        oauth_session, async_get_clientsession(hass)
    )
    hass.data[DOMAIN][entry.entry_id] = {
        "oauth_session": oauth_session,
        "source": source,
    }
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Unload the Microsoft mailbox connection."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
