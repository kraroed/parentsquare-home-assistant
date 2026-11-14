"""Tests for provider-neutral ParentSquare processing."""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from custom_components.parentsquare.classifier import (
    build_notification,
    make_short_summary,
    match_child,
    sender_matches_domains,
)
from custom_components.parentsquare.microsoft_graph import MicrosoftGraphEmailSource
from custom_components.parentsquare.models import (
    ChildMatchRule,
    EmailMessageMetadata,
    NotificationRecord,
)
from custom_components.parentsquare.processing import async_process_message
from custom_components.parentsquare.retention import prune_notifications


def metadata(**overrides: object) -> EmailMessageMetadata:
    values: dict[str, object] = {
        "provider_id": "fixture",
        "message_id": "message-1",
        "sender_address": "notices@school.parentsquare.com",
        "subject": "Reminder for Field Trip",
        "received_at": datetime(2026, 1, 2, tzinfo=UTC),
        "is_read": False,
    }
    values.update(overrides)
    return EmailMessageMetadata(**values)  # type: ignore[arg-type]


def test_sender_domain_allowlist_matches_exact_and_subdomain() -> None:
    assert sender_matches_domains("notices@parentsquare.com", ["parentsquare.com"])
    assert sender_matches_domains(
        "notices@school.parentsquare.com", ["parentsquare.com"]
    )
    assert not sender_matches_domains(
        "notparentsquare.com@example.net", ["parentsquare.com"]
    )
    assert not sender_matches_domains("invalid-address", ["parentsquare.com"])


def test_child_match_requires_exactly_one_rule() -> None:
    message = metadata(subject="Ava: early dismissal tomorrow")
    rules = [
        ChildMatchRule("child_a", ("Ava",)),
        ChildMatchRule("child_b", ("Noah",)),
    ]
    assert match_child(message, rules) == "child_a"
    assert match_child(
        message, [*rules, ChildMatchRule("child_c", ("dismissal",))]
    ) is None
    assert match_child(message, []) is None


def test_metadata_summary_does_not_need_body() -> None:
    assert make_short_summary("Bus route update") == "Bus route update"


def test_short_summary_strips_html_and_truncates() -> None:
    summary = make_short_summary(
        "Notice",
        "<p>School starts late tomorrow.</p><p>Please use the north entrance.</p>",
        max_length=40,
    )
    assert summary == "School starts late tomorrow."
    assert "<p>" not in summary


def test_notification_record_contains_no_body_field() -> None:
    record = build_notification(metadata(), summary="A short notice")
    assert record.summary == "A short notice"
    assert not hasattr(record, "body")
    assert record.deduplication_key == "fixture:message-1"


def test_retention_prunes_old_and_caps_newest() -> None:
    now = datetime(2026, 1, 10, tzinfo=UTC)
    records = [
        NotificationRecord(
            deduplication_key=str(index),
            provider_id="fixture",
            message_id=str(index),
            sender_address="notices@example.test",
            subject=f"Notice {index}",
            received_at=now - timedelta(days=index),
            summary=f"Summary {index}",
        )
        for index in range(5)
    ]
    kept = prune_notifications(records, now=now, retention_days=3, max_records=2)
    assert [record.message_id for record in kept] == ["0", "1"]



class FakeSource:
    """Minimal provider fixture that records body access."""

    provider_id = "fixture"

    def __init__(self, body: str = "A synthetic body sentence.") -> None:
        self.body = body
        self.body_fetches = 0

    async def async_list_folders(self) -> list[tuple[str, str]]:
        return [("folder", "ParentSquare")]

    async def async_get_messages(
        self, folder_id: str, *, privacy_mode: str
    ) -> AsyncIterator[EmailMessageMetadata]:
        yield metadata()

    async def async_get_text_body(self, message_id: str) -> str:
        self.body_fetches += 1
        return self.body


def test_metadata_mode_never_fetches_message_body() -> None:
    source = FakeSource()
    record = asyncio.run(async_process_message(
        source,
        metadata(),
        privacy_mode="metadata",
        sender_domains=["parentsquare.com"],
    ))
    assert record is not None
    assert record.summary == "Reminder for Field Trip"
    assert source.body_fetches == 0


def test_summary_mode_fetches_body_but_does_not_retain_it() -> None:
    source = FakeSource("The school concert begins at 6 PM. Please arrive early.")
    record = asyncio.run(async_process_message(
        source,
        metadata(),
        privacy_mode="summary",
        sender_domains=["parentsquare.com"],
    ))
    assert record is not None
    assert record.summary == "The school concert begins at 6 PM."
    assert source.body_fetches == 1
    assert not hasattr(record, "body")


def test_unapproved_sender_is_ignored_without_body_fetch() -> None:
    source = FakeSource()
    record = asyncio.run(async_process_message(
        source,
        metadata(sender_address="someone@example.test"),
        privacy_mode="summary",
        sender_domains=["parentsquare.com"],
    ))
    assert record is None
    assert source.body_fetches == 0



class FakeResponse:
    """Async context-manager response for Graph adapter tests."""

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    async def json(self) -> dict[str, object]:
        return self.payload


class FakeOAuthSession:
    """OAuth fixture with a synthetic access token."""

    token = {"access_token": "synthetic-token"}

    async def async_ensure_token_valid(self) -> None:
        return None


class FakeWebSession:
    """Capture Graph requests and return a synthetic payload."""

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.requests: list[dict[str, object]] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.requests.append({"url": url, **kwargs})
        return FakeResponse(self.payload)


def test_graph_metadata_request_does_not_select_body_or_preview() -> None:
    async def run() -> list[EmailMessageMetadata]:
        websession = FakeWebSession(
            {
                "value": [
                    {
                        "id": "graph-message-1",
                        "subject": "Synthetic school notice",
                        "from": {
                            "emailAddress": {
                                "name": "School Office",
                                "address": "notices@parentsquare.com",
                            }
                        },
                        "receivedDateTime": "2026-11-13T10:00:00Z",
                        "isRead": False,
                        "internetMessageId": "<synthetic-1@example.test>",
                    }
                ]
            }
        )
        source = MicrosoftGraphEmailSource(FakeOAuthSession(), websession)
        messages = [
            message
            async for message in source.async_get_messages(
                "folder/id", privacy_mode="metadata"
            )
        ]
        selected = websession.requests[0]["params"]["$select"]
        assert "body" not in selected.casefold()
        assert "preview" not in selected.casefold()
        assert websession.requests[0]["url"].endswith("/folder%2Fid/messages")
        return messages

    messages = asyncio.run(run())
    assert len(messages) == 1
    assert messages[0].message_id == "graph-message-1"
    assert messages[0].sender_address == "notices@parentsquare.com"


def test_graph_body_endpoint_is_separate_and_explicit() -> None:
    async def run() -> tuple[str, dict[str, object]]:
        websession = FakeWebSession(
            {"body": {"contentType": "text", "content": "Synthetic summary text"}}
        )
        source = MicrosoftGraphEmailSource(FakeOAuthSession(), websession)
        body = await source.async_get_text_body("message-1")
        return body, websession.requests[0]

    body, request = asyncio.run(run())
    assert body == "Synthetic summary text"
    assert request["params"] == {"$select": "body"}
    assert request["headers"]["Prefer"] == 'outlook.body-content-type="text"'


def test_microsoft_scopes_follow_selected_privacy_mode() -> None:
    from custom_components.parentsquare.const import scopes_for_privacy_mode

    metadata_scopes = scopes_for_privacy_mode("metadata")
    summary_scopes = scopes_for_privacy_mode("summary")
    assert "https://graph.microsoft.com/Mail.ReadBasic" in metadata_scopes
    assert "https://graph.microsoft.com/Mail.Read" not in metadata_scopes
    assert "https://graph.microsoft.com/Mail.Read" in summary_scopes
    assert "https://graph.microsoft.com/Mail.ReadBasic" not in summary_scopes
    assert "offline_access" in metadata_scopes
    assert "offline_access" in summary_scopes
