"""OAuth configuration flow for Microsoft Graph."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CHILD_RULES,
    CONF_FOLDER_ID,
    CONF_PRIVACY_MODE,
    CONF_SENDER_DOMAINS,
    DEFAULT_SENDER_DOMAINS,
    DOMAIN,
    PRIVACY_METADATA,
    PRIVACY_SUMMARY,
    scopes_for_privacy_mode,
)
from .microsoft_graph import MicrosoftGraphEmailSource

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

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the mailbox folder options flow."""
        return ParentSquareOptionsFlow(config_entry)

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


class ParentSquareOptionsFlow(config_entries.OptionsFlow):
    """Select the Outlook folder to monitor."""

    def __init__(self, config_entry) -> None:
        """Initialize options."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Load available folders and save the selected folder."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_FOLDER_ID: user_input[CONF_FOLDER_ID],
                    CONF_SENDER_DOMAINS: user_input[CONF_SENDER_DOMAINS],
                    CONF_CHILD_RULES: user_input.get(CONF_CHILD_RULES, ""),
                },
            )

        implementation = (
            await config_entry_oauth2_flow.async_get_config_entry_implementation(
                self.hass, self.config_entry
            )
        )
        oauth_session = config_entry_oauth2_flow.OAuth2Session(
            self.hass, self.config_entry, implementation
        )
        source = MicrosoftGraphEmailSource(
            oauth_session, async_get_clientsession(self.hass)
        )
        folders = await source.async_list_folders()
        folder_options = {folder_id: name for folder_id, name in folders}

        if not folder_options:
            return self.async_abort(reason="no_mail_folders")

        current_folder = self.config_entry.options.get(
            CONF_FOLDER_ID, "inbox"
        )
        current_domains = self.config_entry.options.get(
            CONF_SENDER_DOMAINS, ", ".join(DEFAULT_SENDER_DOMAINS)
        )
        current_child_rules = self.config_entry.options.get(
            CONF_CHILD_RULES, ""
        )
        default_folder = (
            current_folder
            if current_folder in folder_options
            else next(iter(folder_options))
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_FOLDER_ID, default=default_folder
                    ): vol.In(folder_options),
                    vol.Required(
                        CONF_SENDER_DOMAINS, default=current_domains
                    ): str,
                    vol.Optional(
                        CONF_CHILD_RULES, default=current_child_rules
                    ): str,
                }
            ),
        )
