"""Provider-neutral message processing with privacy-mode enforcement."""

from collections.abc import Sequence

from .classifier import build_notification, make_short_summary, match_child, sender_matches_domains
from .models import ChildMatchRule, EmailMessageMetadata, NotificationRecord, PrivacyMode
from .provider import EmailSource


async def async_process_message(
    source: EmailSource,
    metadata: EmailMessageMetadata,
    *,
    privacy_mode: PrivacyMode,
    sender_domains: Sequence[str],
    child_rules: Sequence[ChildMatchRule] = (),
) -> NotificationRecord | None:
    """Classify and normalize one message without retaining its original body.

    The metadata-only branch deliberately never calls the provider's body method.
    """
    if privacy_mode not in ("metadata", "summary"):
        raise ValueError(f"Unsupported privacy mode: {privacy_mode}")

    if not sender_matches_domains(metadata.sender_address, sender_domains):
        return None

    body: str | None = None
    if privacy_mode == "summary":
        body = await source.async_get_text_body(metadata.message_id)

    summary = make_short_summary(metadata.subject, body)
    child_id = match_child(metadata, child_rules)
    record = build_notification(metadata, summary=summary, child_id=child_id)
    del body
    return record
