# ParentSquare for Home Assistant

An independent Home Assistant integration that tracks ParentSquare notifications delivered to a parent's personal Outlook.com / Live.com mailbox.

> **Development status: email-connector design selected; implementation not yet available.** The repository currently contains project documentation only. It does not yet connect to Microsoft Graph or process email.

## Intended capabilities

- Connect to a personal Microsoft account (Outlook.com, Hotmail, or Live.com) using Microsoft OAuth.
- Monitor a user-selected Outlook folder for ParentSquare notification emails.
- Identify school, sender, date, subject, and child association where the email provides enough information.
- Show concise notification summaries in Home Assistant.
- Expose integration status, latest notification, and unread/new-message counters.
- Keep the full email in Outlook; do not create a duplicate archive of message bodies or attachments.
- Provide configurable notification delivery and a family dashboard.

## Selected access method: Microsoft Graph email

This project will not sign in to ParentSquare, scrape ParentSquare pages, or call undocumented ParentSquare endpoints. It will read notification emails that ParentSquare has already delivered to the user's own mailbox, after the user authorizes the integration with Microsoft.

The selected account type is a **personal Microsoft account**. Microsoft documents Outlook mail API access for personal Microsoft accounts and supports delegated `Mail.ReadBasic` and `Mail.Read` permissions.

### Permission and privacy modes

- **Metadata-only mode (default target):** request delegated `Mail.ReadBasic`. This can read basic message properties such as sender, subject, and received time, but does not expose the message body or preview body. The Home Assistant summary will therefore be based on the subject and available metadata.
- **Email-preview mode (optional):** request delegated `Mail.Read` only if the user chooses body-based summaries. This grants read access to the signed-in user's mailbox, not just the selected folder. The integration will query only the configured ParentSquare folder, avoid fetching attachments, and retain only the configured short summary and minimal metadata.

The folder filter is an application behavior, not a Microsoft-enforced permission boundary. Users should understand the mailbox-level scope shown on Microsoft's consent screen before authorizing either mode. The integration will never request send, delete, or mail-write permissions.

## Planned setup

1. Create or select an Outlook folder for ParentSquare notifications.
2. Configure an Outlook rule to move ParentSquare notification emails into that folder.
3. Add the integration in Home Assistant and complete Microsoft OAuth sign-in.
4. Select the folder and choose metadata-only or optional email-preview mode.
5. Verify message classification using real notifications before enabling automations.

Authentication will use Home Assistant's OAuth2 and Application Credentials support with a user-present authorization-code flow. The integration will never request your Microsoft account password or MFA code. If Microsoft requires a client secret for the selected redirect/client type, it will be stored through Home Assistant Application Credentials, never in repository files or logs. The exact redirect and app-registration requirements will be verified before live authentication is enabled.

## Privacy and security goals

- Never commit credentials, authorization codes, refresh tokens, real email contents, student names, or school identifiers.
- Store OAuth tokens using Home Assistant's config-entry credential storage.
- Request only delegated read permissions; never request mail send or write access.
- Default to metadata-only processing.
- Do not fetch attachments.
- Do not retain full message bodies or HTML.
- Use synthetic test data in the repository and test suite.
- Provide a way to clear locally retained notification metadata.
- Do not send family communication content to third-party summarization services.

## Development status

No live Microsoft Graph connection, OAuth flow, entities, or notifications are included yet. Until the integration is implemented and validated, do not enter Microsoft credentials or tokens into this project.

## Disclaimer

This project is independent and is not affiliated with, endorsed by, or sponsored by ParentSquare, Inc. or Microsoft. ParentSquare, Outlook, and related marks belong to their respective owners. Users are responsible for complying with applicable service terms, school policies, privacy requirements, and applicable law.An independent, multi-provider Home Assistant integration that tracks ParentSquare notifications delivered to a parent's personal email mailbox.

> **Development status: multi-provider architecture planned; implementation not yet available.** The repository currently contains project documentation only. It does not yet connect to email providers or process messages.

## Intended capabilities

- Connect to common personal email providers through provider-specific, read-only adapters.
- Initial provider targets: Gmail, Outlook.com/Hotmail/Live.com, Yahoo/AOL, iCloud Mail, and generic IMAP-compatible providers (including Fastmail, Zoho, GMX, and Proton Mail Bridge where supported).
- Monitor a user-selected label or folder for ParentSquare notification emails.
- Identify school, sender, date, subject, and child association where the email provides enough information.
- Show concise notification summaries in Home Assistant.
- Expose integration status, latest notification, and unread/new-message counters.
- Keep the full email in the provider's mailbox; do not create a duplicate archive of message bodies or attachments.
- Provide configurable notification delivery and a family dashboard.

## Email access architecture

This project will not sign in to ParentSquare, scrape ParentSquare pages, or call undocumented ParentSquare endpoints. It reads notification emails already delivered to the user's own mailbox, after the user authorizes the selected email provider.

Provider access is implemented through separate adapters behind a common email-source interface. OAuth/API providers use their official APIs where practical; other providers use standards-based IMAP with the strongest authentication they support. Provider capabilities differ and will be clearly disclosed during setup. See [the multi-provider architecture](docs/email-provider-architecture.md).

### Permission and privacy modes

- **Metadata-only mode (default):** retrieve only sender, subject, received time, message identifiers, and read status where available. Do not request or fetch message bodies or attachments.
- **Short-summary mode (optional):** retrieve message text only when the user explicitly enables it, extract a short local summary, and discard the original body. Never fetch attachments or transmit family message content to an external summarization service.

The selected folder/label is an application-level query filter, not necessarily a provider-enforced permission boundary. OAuth scopes may grant access to more of the mailbox than the integration queries. The setup flow must explain each provider's actual permission scope before authorization. The integration will never request send, delete, or mail-write permissions.

## Planned setup

1. Create or select a dedicated folder/label for ParentSquare notifications.
2. Configure a provider-side rule/filter to route ParentSquare emails into it where supported.
3. Add the integration in Home Assistant and select the email provider.
4. Complete the provider's supported authorization flow and select the folder/label.
5. Choose metadata-only or optional short-summary mode.
6. Verify message classification using real notifications before enabling automations.

Authentication will use provider-specific OAuth or secure IMAP credentials, stored through Home Assistant's credential/config-entry facilities. The integration will never request ParentSquare credentials. Exact permissions and setup steps will be documented per provider.

## Privacy and security goals

- Never commit credentials, authorization codes, refresh tokens, real email contents, student names, or school identifiers.
- Store OAuth tokens using Home Assistant's config-entry credential storage.
- Request only delegated read permissions; never request mail send or write access.
- Default to metadata-only processing.
- Do not fetch attachments.
- Do not retain full message bodies or HTML.
- Use synthetic test data in the repository and test suite.
- Provide a way to clear locally retained notification metadata.
- Do not send family communication content to third-party summarization services.

## Development status

No live Microsoft Graph connection, OAuth flow, entities, or notifications are included yet. Until the integration is implemented and validated, do not enter Microsoft credentials or tokens into this project.

## Disclaimer

This project is independent and is not affiliated with, endorsed by, or sponsored by ParentSquare, Inc. or Microsoft. ParentSquare, Outlook, and related marks belong to their respective owners. Users are responsible for complying with applicable service terms, school policies, privacy requirements, and applicable law.
