# Outlook email connector design

## Account profile

The target account for the initial implementation is a consumer Microsoft account (@live.com, @outlook.com, or @hotmail.com). Use the Microsoft identity platform consumer authority:

`https://login.microsoftonline.com/consumers`

The app registration must support personal Microsoft accounts. Do not use a tenant-specific work/school authority for this account.

## Authentication

Use Home Assistant's Application Credentials and OAuth2 config-flow helpers. The implementation must use a user-present authorization-code flow and must never use username/password authentication, resource-owner-password credentials, or client credentials. Never ask the user for their Microsoft password or MFA code in Home Assistant.

The app registration's platform type and redirect URI must match Home Assistant's callback behavior. Prefer the Home Assistant My redirect callback when available; verify the exact redirect URI against current Home Assistant and Microsoft requirements before publishing setup instructions. If a confidential web-client registration is required, the user-created client secret must be stored only in Home Assistant Application Credentials. Do not commit or log it.

## Graph permissions

### Default metadata-only mode

Request delegated `Mail.ReadBasic` and only the minimum OpenID scopes required by the selected authentication library. Microsoft documents that delegated `Mail.ReadBasic` is available for personal Microsoft accounts and excludes message body, previewBody, attachments, and extended properties.

Read only the fields required for notification tracking, such as id, subject, from, receivedDateTime, isRead, and internetMessageId (if returned for the endpoint and scope).

Do not request or fetch body, preview body, MIME content, or attachments in this mode. A concise summary is limited to the subject and available metadata.

### Optional email-preview mode

If the user explicitly enables body-based summaries, request delegated `Mail.Read`. This is a higher permission that permits reading the signed-in user's mailbox. Microsoft does not enforce a folder-only boundary for this delegated permission.

In this mode:
- Query only the folder selected by the user.
- Select only required message properties.
- Never fetch attachments or MIME content.
- Convert HTML to plain text locally.
- Limit the extracted preview to a small configurable character count.
- Do not persist the original body or HTML.
- Do not transmit message text to external summarization services.
- Clearly explain the mailbox-wide delegated permission before the user consents.

Never request `Mail.ReadWrite`, `Mail.Send`, or application permissions.

## Folder strategy

The user creates an Outlook folder and an Outlook rule to route ParentSquare notifications into it. The integration lists folders using Graph and lets the user select the target folder. The selected folder ID is stored in the config entry.

The folder selection is a query restriction implemented by this integration, not a security boundary imposed by Microsoft Graph. The UI and documentation must say so.

## Polling and deduplication

Use bounded polling with a configurable interval and conservative page sizes. Prefer Microsoft Graph message delta tracking for the selected folder if it behaves consistently for consumer accounts and the required delegated scope. Otherwise use a bounded received-time query with an overlap window.

Deduplicate by Graph message ID and, where useful, Internet Message ID. Handle token expiration, throttling (429 / Retry-After), transient errors, deleted/moved messages, and invalid delta tokens. Never mark Outlook messages read or move/delete them.

## Home Assistant data model

Initial entities should remain minimal:
- Integration coordinator status.
- New/unread notification count for the selected folder.
- Latest notification subject / concise summary.
- Latest notification sender and received time.
- Optional per-child counters only after the user configures explicit matching rules and the email content reliably supports the association.

Do not infer a child's identity from ambiguous email text. Allow user-defined matching rules, and represent uncertain associations as unassigned.

## Retention

Store only deduplication keys and minimal notification metadata needed for sensors and notifications. Do not retain full bodies, HTML, attachments, or conversation threads. Provide a clear-history action and bounded retention for notification records.

## Test strategy

Use synthetic .eml or normalized Graph message fixtures only. Include tests for:
- ParentSquare-like sender and subject variations.
- HTML and plain-text email normalization in preview mode.
- Metadata-only mode never requesting body or previewBody.
- Child matching, ambiguity, and unassigned messages.
- Duplicate delivery and overlapping polling windows.
- Pagination, throttling, token expiry, and invalid delta tokens.
- No message mutation (read flag, move, delete, send).
- No sensitive fixture data in logs.

## Implementation status

This document describes the planned Microsoft Graph adapter. The repository does not yet implement Microsoft OAuth, Graph requests, folder discovery, polling, or live mailbox access. The provider-neutral processing layer is in place; Microsoft Graph is the next provider milestone.

A configured sender-domain allow-list is a filtering mechanism only. It is not, by itself, proof of sender authenticity.

