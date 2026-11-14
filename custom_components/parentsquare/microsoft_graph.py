"""Microsoft Graph read-only email adapter."""

from collections.abc import AsyncIterator, Sequence
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from aiohttp import ClientSession

from .models import EmailMessageMetadata, PrivacyMode

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
MESSAGE_FIELDS = (
    "id,subject,from,receivedDateTime,isRead,internetMessageId,parentFolderId"
)
PAGE_SIZE = 50
MAX_PAGES = 2


class MicrosoftGraphEmailSource:
    """Read Outlook folders and messages without mutating the mailbox."""

    provider_id = "microsoft"

    def __init__(self, oauth_session: Any, websession: ClientSession) -> None:
        self._oauth_session = oauth_session
        self._websession = websession

    async def _async_get_json(
        self, url: str, *, params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make one authenticated Graph GET request."""
        await self._oauth_session.async_ensure_token_valid()
        access_token = self._oauth_session.token["access_token"]
        request_headers = {"Authorization": f"Bearer {access_token}"}
        if headers:
            request_headers.update(headers)

        async with self._websession.get(
            url, params=params, headers=request_headers
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def async_list_folders(self) -> Sequence[tuple[str, str]]:
        """Return root-level Outlook folders for user selection."""
        url = f"{GRAPH_ROOT}/me/mailFolders"
        params = {"$select": "id,displayName", "$top": "100"}
        folders: list[tuple[str, str]] = []
        while url:
            payload = await self._async_get_json(url, params=params)
            params = None
            for folder in payload.get("value", []):
                folder_id = folder.get("id")
                display_name = folder.get("displayName")
                if folder_id and display_name:
                    folders.append((str(folder_id), str(display_name)))
            url = payload.get("@odata.nextLink", "")
        return folders

    async def async_get_messages(
        self, folder_id: str, *, privacy_mode: PrivacyMode
    ) -> AsyncIterator[EmailMessageMetadata]:
        """Yield recent metadata without requesting body or preview properties."""
        if privacy_mode not in ("metadata", "summary"):
            raise ValueError(f"Unsupported privacy mode: {privacy_mode}")

        encoded_folder = quote(folder_id, safe="")
        url = f"{GRAPH_ROOT}/me/mailFolders/{encoded_folder}/messages"
        params = {
            "$select": MESSAGE_FIELDS,
            "$top": str(PAGE_SIZE),
            "$orderby": "receivedDateTime desc",
        }

        for _ in range(MAX_PAGES):
            payload = await self._async_get_json(url, params=params)
            params = None
            for item in payload.get("value", []):
                yield self._normalize_message(item, folder_id)
            url = payload.get("@odata.nextLink", "")
            if not url:
                break

    async def async_get_text_body(self, message_id: str) -> str:
        """Fetch message text only when the caller has opted into summaries."""
        encoded_message = quote(message_id, safe="")
        payload = await self._async_get_json(
            f"{GRAPH_ROOT}/me/messages/{encoded_message}",
            params={"$select": "body"},
            headers={"Prefer": 'outlook.body-content-type="text"'},
        )
        body = payload.get("body") or {}
        return str(body.get("content") or "")

    @staticmethod
    def _normalize_message(
        item: dict[str, Any], folder_id: str
    ) -> EmailMessageMetadata:
        """Normalize a Graph message response without copying body fields."""
        sender = (item.get("from") or {}).get("emailAddress") or {}
        received = item.get("receivedDateTime")
        if received:
            received_at = datetime.fromisoformat(
                str(received).replace("Z", "+00:00")
            )
            if received_at.tzinfo is None:
                received_at = received_at.replace(tzinfo=timezone.utc)
        else:
            received_at = datetime.now(timezone.utc)

        return EmailMessageMetadata(
            provider_id="microsoft",
            message_id=str(item["id"]),
            sender_address=str(sender.get("address") or ""),
            sender_name=sender.get("name"),
            subject=str(item.get("subject") or ""),
            received_at=received_at,
            internet_message_id=item.get("internetMessageId"),
            folder_id=folder_id,
            is_read=item.get("isRead"),
        )
