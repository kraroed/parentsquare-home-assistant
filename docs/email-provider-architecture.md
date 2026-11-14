# Multi-provider email architecture

## Product goal

Support common personal mailbox providers without coupling ParentSquare notification parsing to one vendor API. All providers feed the same normalized notification pipeline and expose the same Home Assistant entities and options.

## Initial provider targets

1. **Gmail / Google** — Gmail API with Google OAuth. Metadata-only mode should use the narrowest metadata scope that supports the required fields and label filtering. Short-summary mode requires an explicitly consented read-only mail scope.
2. **Microsoft Outlook.com / Hotmail / Live.com** — Microsoft Graph with consumer-account OAuth. Metadata-only mode uses delegated `Mail.ReadBasic`; short-summary mode uses delegated `Mail.Read`. Explain that the folder filter does not constrain the mailbox-wide delegated permission.
3. **Yahoo Mail and AOL Mail** — prefer supported OAuth2 access where available; otherwise offer IMAP only when the account/provider supports an appropriate modern or app-password authentication method. Do not assume ordinary account-password IMAP is available.
4. **Apple iCloud Mail** — IMAP with an Apple app-specific password, subject to Apple's current account security requirements. Store the credential securely and never log it.
5. **Generic IMAP** — user-configurable IMAP host, port, TLS mode, and supported authentication. This covers providers such as Fastmail, Zoho, GMX, and many ISP/custom-domain mailboxes. Proton Mail is supported only through a separately running Proton Mail Bridge or another officially supported IMAP bridge; do not claim direct Proton IMAP access.

The list is a practical compatibility target, not a definitive statistical ranking. Providers publish inconsistent user counts, and market-share estimates differ by methodology. The design prioritizes the largest mainstream ecosystems plus a generic protocol adapter for broad coverage.

## Shared provider interface

Define a provider-independent interface for:
- Establishing and refreshing authorization.
- Listing folders/labels and selecting the ParentSquare destination.
- Fetching message metadata.
- Fetching message text only in short-summary mode.
- Polling or syncing new messages with pagination and deduplication.
- Reporting provider capabilities, errors, throttling, and reauthorization requirements.

Normalize messages into a common internal model: provider message ID, stable deduplication key, sender, subject, received timestamp, read/unread state if available, folder/label ID, and optional transient plain-text content. Provider-specific IDs and capabilities remain internal.

## Privacy modes

### Metadata-only (default)

Fetch only the fields needed for sender, subject, date, identifier, folder/label, and status. Never fetch body, preview text, MIME content, or attachments. Build the Home Assistant summary from subject and metadata only.

### Short-summary (explicit opt-in)

Fetch only the text body needed for a short summary. Parse HTML locally to plain text, strip quoted reply chains and signatures where feasible, cap the text length, and produce a concise excerpt locally. Do not call external AI/summarization services. Do not persist the original HTML or body; discard it after processing. Store only the resulting short summary and minimal metadata according to retention settings.

Provider permissions differ. The config flow and documentation must disclose the actual scope, including any mailbox-wide permissions, before the user authorizes. A folder/label selection is an application-level query filter and must never be presented as a provider-enforced security boundary unless the provider explicitly guarantees it.

## Credential handling

- Prefer official provider OAuth/API access where practical.
- Use authorization-code flows with PKCE or the provider's recommended user-present OAuth mechanism.
- Use Home Assistant Application Credentials and config-entry storage for OAuth secrets/tokens where supported.
- For IMAP, use TLS and provider-specific app passwords or OAuth tokens where supported; never ask for a primary account password if a safer supported method exists.
- Never log credentials, authorization codes, access/refresh tokens, message bodies, or student information.
- Never request send, delete, move, or mail-write permissions. The integration is read-only and must not mark messages as read.

## Folder/label filtering

Users create a dedicated folder or label and configure a provider-side rule to route ParentSquare messages there. The integration queries only that destination. Explain that this reduces processing but does not necessarily reduce the underlying OAuth permission scope.

## Delivery and normalization

Provider adapters emit normalized messages into one provider-neutral classifier. The classifier identifies ParentSquare senders and message types using configurable sender/domain rules and synthetic-tested patterns. Child association is based only on explicit user-configured rules or unambiguous fields; ambiguous messages remain unassigned.

## Implementation order

1. Build the provider-neutral models, coordinator contract, classifier, retention policy, and synthetic tests.
2. Implement Microsoft Graph first for the maintainer's personal Live.com account.
3. Implement Gmail API as the next major OAuth provider.
4. Add generic IMAP with robust TLS, app-password/OAuth support, and provider presets.
5. Validate Yahoo/AOL and iCloud against current provider authentication requirements, then add presets/adapters.
6. Add optional Proton Mail Bridge guidance and test interoperability without claiming direct Proton service support.

## Test requirements

- Every provider adapter passes the same normalized contract tests.
- Metadata-only mode never fetches body, preview, MIME, or attachments.
- Short-summary mode fetches text only and discards raw content after processing.
- No provider adapter sends, deletes, moves, or marks messages read.
- Test OAuth refresh, revoked consent, invalid credentials, pagination, throttling, reconnect, and duplicate delivery.
- Test HTML/plain text parsing, sender variations, missing fields, ambiguous child association, and retention cleanup.
- All fixtures are synthetic; logs contain no real email or student data.

## Foundation implementation status (November 2026)

The first provider-neutral code layer now exists under `custom_components/parentsquare/`:

- `models.py` defines normalized metadata, explicit child-match rules, and body-free notification records.
- `provider.py` defines the read-only email-source adapter contract.
- `processing.py` enforces the privacy-mode branch: metadata-only processing never calls the body-fetch method; summary mode calls it only after opt-in.
- `classifier.py` provides explicit sender-domain filtering, conservative child matching, local HTML-to-text extraction, and short summaries.
- `retention.py` applies age and item-count limits.
- Synthetic tests cover these behaviors.

This is a development foundation, not a finished Home Assistant integration. There is not yet a config flow, provider authentication, polling coordinator, entity platform, notification service, or live provider adapter.

### Sender filtering limitation

The configured sender-domain list is a classification/filtering rule, not proof that an email was cryptographically sent by ParentSquare. Do not treat a matching sender address alone as authentication. Provider-side message authenticity signals may be evaluated separately where safely available.



## Current Microsoft milestone

The repository now includes a working code path for Home Assistant OAuth/PKCE setup, selected Microsoft Graph permissions, Outlook folder selection, configurable sender-domain filtering, optional explicit child matching, periodic polling, bounded local persistence, and unread/latest/per-child sensors. This milestone is implemented against synthetic fixtures and current Home Assistant OAuth patterns. It is not yet live-account validated, and the other provider adapters remain planned.
