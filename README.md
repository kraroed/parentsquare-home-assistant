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

Authentication will use a public-client OAuth authorization-code flow with PKCE where supported. No Microsoft account password or client secret will be stored by the integration. The final redirect and app-registration requirements will be documented before live authentication is enabled.

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
