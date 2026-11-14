"""ParentSquare email classification and local summary helpers."""

import re
from collections.abc import Iterable, Sequence
from html.parser import HTMLParser

from .const import BODY_MAX_LENGTH, SUMMARY_MAX_LENGTH
from .models import ChildMatchRule, EmailMessageMetadata, NotificationRecord


class _TextExtractor(HTMLParser):
    """Convert HTML to plain text without retaining markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def sender_matches_domains(sender_address: str, domains: Iterable[str]) -> bool:
    """Check the sender domain against an explicit allow-list."""
    address = sender_address.strip().lower()
    if "@" not in address:
        return False
    sender_domain = address.rsplit("@", 1)[1].rstrip(".")
    allowed = {domain.strip().lower().lstrip("@").rstrip(".") for domain in domains}
    return any(
        sender_domain == domain or sender_domain.endswith(f".{domain}")
        for domain in allowed
        if domain
    )


def match_child(
    metadata: EmailMessageMetadata, rules: Sequence[ChildMatchRule]
) -> str | None:
    """Return a child ID only when exactly one configured rule matches."""
    haystack = f"{metadata.subject} {metadata.sender_address}".casefold()
    matched_ids = {
        rule.child_id
        for rule in rules
        if rule.child_id
        and rule.terms
        and any(
            term.strip().casefold() in haystack
            for term in rule.terms
            if term.strip()
        )
    }
    return next(iter(matched_ids)) if len(matched_ids) == 1 else None


def make_short_summary(
    subject: str, body: str | None = None, *, max_length: int = SUMMARY_MAX_LENGTH
) -> str:
    """Create a small local summary and discard the source text after return."""
    if not body:
        return _truncate(subject.strip(), max_length)

    bounded_body = body[:BODY_MAX_LENGTH]
    if "<" in bounded_body and ">" in bounded_body:
        parser = _TextExtractor()
        try:
            parser.feed(bounded_body)
            text = " ".join(parser.parts)
        except Exception:  # noqa: BLE001 - malformed email HTML is expected input
            text = re.sub(r"<[^>]*>", " ", bounded_body)
    else:
        text = bounded_body

    text = re.split(
        r"(?im)^\s*(?:[- ]{2,}|on .+wrote:|from: .+)", text, maxsplit=1
    )[0]
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        text = subject.strip()
    sentence = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
    return _truncate(sentence or text, max_length)


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max(0, max_length - 1)].rstrip() + "…"


def build_notification(
    metadata: EmailMessageMetadata,
    *,
    summary: str,
    child_id: str | None = None,
) -> NotificationRecord:
    """Build a body-free record from normalized metadata and a short summary."""
    stable_id = metadata.internet_message_id or metadata.message_id
    return NotificationRecord(
        deduplication_key=f"{metadata.provider_id}:{stable_id}",
        provider_id=metadata.provider_id,
        message_id=metadata.message_id,
        sender_address=metadata.sender_address,
        subject=metadata.subject,
        received_at=metadata.received_at,
        summary=_truncate(summary.strip(), SUMMARY_MAX_LENGTH),
        child_id=child_id,
        is_read=metadata.is_read,
    )
