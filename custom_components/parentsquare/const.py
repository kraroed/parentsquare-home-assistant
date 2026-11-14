"""Constants for the ParentSquare integration."""

from datetime import timedelta

DOMAIN = "parentsquare"
CONF_PROVIDER = "provider"
CONF_PRIVACY_MODE = "privacy_mode"
CONF_FOLDER_ID = "folder_id"
CONF_SENDER_DOMAINS = "sender_domains"
CONF_CHILD_RULES = "child_rules"

PROVIDER_MICROSOFT = "microsoft"
PROVIDER_GMAIL = "gmail"
PROVIDER_YAHOO = "yahoo"
PROVIDER_ICLOUD = "icloud"
PROVIDER_IMAP = "imap"
PROVIDER_PROTON_BRIDGE = "proton_bridge"

PRIVACY_METADATA = "metadata"
PRIVACY_SUMMARY = "summary"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
DEFAULT_RETENTION_DAYS = 30
DEFAULT_MAX_NOTIFICATIONS = 250
DEFAULT_SENDER_DOMAINS = ("parentsquare.com",)
SUMMARY_MAX_LENGTH = 280
BODY_MAX_LENGTH = 8000


def scopes_for_privacy_mode(privacy_mode: str) -> tuple[str, ...]:
    """Return the narrowest Microsoft Graph delegated scopes for a mode."""
    if privacy_mode == PRIVACY_METADATA:
        return ("offline_access", "https://graph.microsoft.com/Mail.ReadBasic")
    if privacy_mode == PRIVACY_SUMMARY:
        return ("offline_access", "https://graph.microsoft.com/Mail.Read")
    raise ValueError(f"Unsupported privacy mode: {privacy_mode}")
