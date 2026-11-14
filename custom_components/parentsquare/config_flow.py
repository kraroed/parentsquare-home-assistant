"""OAuth configuration flow for Microsoft Graph."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult
from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    DOMAIN,
    PRIVACY_METADATA,
    PRIVACY_SUMMARY,
    CONF_PRIVACY_MODE,
    scopes_for_privacy_mode,
)

_LOGGER = logging.getLogger(__name__)


class ParentSquareConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Configure the Microsoft mailbox connection."""

    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Initialize the flow."""
        super().__init__()
        self._privacy_mode = PRIVACY_METADATA

    @property
    def logger(self) -> logging.Logger:
        """Return the integration logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Request only the permission selected before account linking."""
        return {
            "scope": " ".join(scopes_for_privacy_mode(self._privacy_mode)),
            "prompt": "select_account",
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for privacy mode before redirecting to Microsoft."""
        if self.source == SOURCE_REAUTH:
            entry = self.hass.config_entries.async_get_entry(
                self.context["entry_id"]
            )
            if entry is not None:
                self._privacy_mode = entry.data.get(
                    CONF_PRIVACY_MODE, PRIVACY_METADATA
                )
            return await super().async_step_user()

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_PRIVACY_MODE, default=PRIVACY_METADATA
                        ): vol.In(
                            {
                                PRIVACY_METADATA: "Metadata only (recommended)",
                                PRIVACY_SUMMARY: "Short summaries (reads message text)",
                            }
                        )
                    }
                ),
            )

        self._privacy_mode = user_input[CONF_PRIVACY_MODE]
        return await super().async_step_user()

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication while preserving the selected privacy mode."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm that Microsoft needs to be linked again."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    async def async_oauth_create_entry(
        self, data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create or update the single Microsoft mailbox entry."""
        await self.async_set_unique_id("microsoft_graph")
        data[CONF_PRIVACY_MODE] = self._privacy_mode

        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data_updates=data
            )

        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title="Outlook.com (Microsoft)", data=data
        )
