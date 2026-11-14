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

This document describes the planned Microsoft Graph adapter. The repository now includes Microsoft OAuth authorization-code flow with PKCE, Home Assistant Application Credentials, metadata-only versus short-summary scope selection, reauthentication, and an Outlook folder-selection options flow. OAuth has not yet been exercised against a live personal Microsoft account. Polling, persistent notification storage, sensors, and live mailbox validation remain future work.

A configured sender-domain allow-list is a filtering mechanism only. It is not, by itself, proof of sender authenticity.

## Microsoft Graph adapter implementation

The repository now includes `custom_components/parentsquare/microsoft_graph.py`, a read-only adapter that:

- Lists root-level Outlook folders using `GET /me/mailFolders`.
- Reads selected-folder messages using `GET /me/mailFolders/{id}/messages`.
- Uses an explicit `$select` list for message metadata; it does not request `body` or `bodyPreview`.
- Follows Graph pagination for a bounded number of pages.
- Fetches `body` only through a separate method intended for explicit short-summary mode.
- Uses the Home Assistant OAuth session's token-refresh helper before each request.
- Contains no send, move, delete, or mark-as-read operations.

The adapter's synthetic tests verify the metadata query excludes body/preview fields and that body retrieval is a separate explicit request. Root-folder listing does not yet recurse into nested folders. OAuth and folder-selection code are now present, but have not been validated against a live Microsoft account. Polling coordinator, persistent notification storage, and entities remain future work.



## OAuth setup implementation

The config flow asks for the privacy mode before redirecting to Microsoft. Metadata-only requests delegated `Mail.ReadBasic`; optional short-summary mode requests delegated `Mail.Read`. Both request `offline_access` for refresh tokens. The flow uses Home Assistant's Application Credentials integration and authorization-code PKCE as a public client. It does not ask for a Microsoft password or client secret.

The integration supports one Microsoft mailbox entry. After linking, open the integration's options to select the Outlook folder that receives ParentSquare notification emails. The selected folder is a query filter, not a Microsoft permission boundary.

Before publishing installation instructions, the OAuth callback and app-registration platform settings must be verified end-to-end with a real consumer Microsoft account. The current implementation has not yet passed that live test.


## Polling and sensor implementation

The initial coordinator now polls the selected folder on a five-minute interval, reads a bounded recent message window, deduplicates by provider ID plus Internet Message ID (or Graph message ID), refreshes read/unread state for tracked messages, and persists only normalized metadata plus the configured short summary. Storage is bounded to 30 days and 250 records. Original email bodies are not stored.

The options flow allows the user to configure:
- The Outlook folder to monitor.
- A comma-separated sender-domain allow-list (default: `parentsquare.com`).
- Explicit child matching rules, one per line in the form `Child label: keyword1, keyword2`.

A sender-domain match is a filter, not cryptographic sender authentication. Child matching is intentionally conservative: a notification is assigned only when exactly one configured child rule matches. In metadata-only mode, matching uses the subject; in short-summary mode, it can also use the locally extracted summary. Ambiguous messages remain unassigned.

The initial sensors expose the unread count in the retained recent window, the latest notification subject and summary attributes, and one unread counter for each configured child rule. The unread count is not a provider-wide unread total; it is limited to messages tracked in the bounded recent window.

This code has passed synthetic tests and static linting, but still needs full Home Assistant runtime validation and a live personal Microsoft account test before release.
