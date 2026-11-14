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
SUMMARY_MAX_LENGTH = 280
BODY_MAX_LENGTH = 8000
