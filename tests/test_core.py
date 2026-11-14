"""Tests for provider-neutral ParentSquare processing."""

import asyncio
from datetime import datetime, timedelta, timezone

from custom_components.parentsquare.classifier import (
    build_notification,
    make_short_summary,
    match_child,
    sender_matches_domains,
)
from custom_components.parentsquare.processing import async_process_message
from custom_components.parentsquare.models import (
    ChildMatchRule,
    EmailMessageMetadata,
    NotificationRecord,
)
from custom_components.parentsquare.retention import prune_notifications


def metadata(**overrides: object) -> EmailMessageMetadata:
    values: dict[str, object] = {
        "provider_id": "fixture",
        "message_id": "message-1",
        "sender_address": "notices@school.parentsquare.com",
        "subject": "Reminder for Field Trip",
        "received_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
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
    now = datetime(2026, 1, 10, tzinfo=timezone.utc)
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

    async def async_get_messages(self, folder_id: str, *, privacy_mode: str):
        if False:
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
