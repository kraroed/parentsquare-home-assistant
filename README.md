# ParentSquare for Home Assistant

An independent Home Assistant integration that tracks ParentSquare notification emails delivered to a user's own mailbox.

> **Development status: provider foundation and Microsoft Graph adapter in progress.** The repository includes the provider-neutral processing layer and a tested, read-only Graph adapter. OAuth setup, polling, Home Assistant entities, and live mailbox validation are not complete; the integration is not yet ready to install.

## Goals

- Track ParentSquare notifications from email already delivered to the user's mailbox.
- Show notification metadata and concise summaries in Home Assistant.
- Associate messages with a child only through explicit, unambiguous user rules.
- Keep original messages in the user's mailbox; do not build a duplicate email archive.
- Support multiple providers through independent adapters and a shared processing pipeline.

## Planned email providers

1. Gmail through the Gmail API and Google OAuth.
2. Outlook.com, Hotmail, and Live.com through Microsoft Graph consumer OAuth.
3. Yahoo Mail, using supported OAuth or secure IMAP authentication.
4. Apple iCloud Mail through IMAP and an Apple app-specific password, subject to Apple's current requirements.
5. Proton Mail only through Proton Mail Bridge or another officially supported IMAP bridge.
6. Generic IMAP for compatible Fastmail, Zoho, GMX, AOL, ISP, and custom-domain mailboxes.

This is a practical compatibility target, not a statistical ranking of providers. Provider capabilities and authentication requirements vary and will be documented before each adapter is advertised as supported.

## Privacy modes

- **Metadata-only (default):** retrieve sender, subject, received time, message identifiers, folder/label, and read state where available. Never fetch body text, previews, MIME content, or attachments.
- **Short-summary (optional):** only after explicit opt-in, fetch message text, convert HTML locally, extract a short summary locally, and discard the original body. Do not fetch attachments or send message content to external AI services.

A selected folder or label is an application-level query filter. It is not necessarily a provider-enforced security boundary. OAuth permissions may apply to more of the mailbox than the folder being queried. The setup flow must disclose each provider's actual permission scope before authorization.

The integration will not request mail send, delete, move, or write permissions, and will not mark messages as read.

## Why email, not ParentSquare login

This project does not sign in to ParentSquare, scrape ParentSquare pages, or call undocumented ParentSquare endpoints. It processes notification emails that ParentSquare has already delivered to the user's mailbox, after the user authorizes the selected email provider.

## Development plan

1. Provider-neutral models, classification, child matching, retention, and synthetic tests. (Implemented.)
2. Microsoft Graph read-only adapter and synthetic API tests. (Implemented; OAuth and live integration remain.)
3. Complete Microsoft OAuth, folder selection, polling coordinator, and Home Assistant entities.
4. Gmail API.
5. Generic IMAP and validated provider presets.
6. Yahoo/AOL and iCloud authentication validation.
7. Proton Bridge interoperability guidance and testing.

See [multi-provider architecture](docs/email-provider-architecture.md) and [Outlook design](docs/outlook-email-architecture.md).

## Security

- Never commit credentials, authorization codes, refresh tokens, real email contents, student names, or school identifiers.
- Use Home Assistant Application Credentials and config-entry credential storage for OAuth.
- Use TLS and provider-specific app passwords/OAuth for IMAP where supported.
- Never log tokens, message bodies, or family/student information.
- Use synthetic fixtures only.
- Retain only minimal metadata and the configured short summary; provide bounded retention and a clear-history option in the completed integration.

## Disclaimer

This independent project is not affiliated with, endorsed by, or sponsored by ParentSquare, Inc. or Microsoft. ParentSquare, Outlook, and related marks belong to their respective owners. Users are responsible for complying with applicable service terms, school policies, privacy requirements, and applicable law.
