"""Provider adapter contract shared by email integrations."""

from collections.abc import AsyncIterator, Sequence
from typing import Protocol

from .models import EmailMessageMetadata, PrivacyMode


class EmailSource(Protocol):
    """Read-only email source contract.

    Implementations must not send, move, delete, or mark messages as read.
    Metadata mode must not request message body or preview fields.
    """

    provider_id: str

    async def async_list_folders(self) -> Sequence[tuple[str, str]]:
        """Return folder/label identifiers and display names."""

    async def async_get_messages(
        self, folder_id: str, *, privacy_mode: PrivacyMode
    ) -> AsyncIterator[EmailMessageMetadata]:
        """Yield messages from the selected folder, newest first."""

    async def async_get_text_body(self, message_id: str) -> str:
        """Fetch text only; callers may use this only in summary mode."""
