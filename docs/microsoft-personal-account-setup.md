# Microsoft personal-account setup

This guide is for Outlook.com, Hotmail, and Live.com personal accounts. It is not for work or school Microsoft 365 tenants.

The integration uses Home Assistant's OAuth 2.0 flow with PKCE. Do not share your Microsoft password, MFA code, client ID/secret, authorization code, or token in GitHub issues or chat.

## 1. Register an application

1. Open [Microsoft Entra app registrations](https://entra.microsoft.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade).
2. Create a new registration.
3. Choose the supported account type **Personal Microsoft accounts only**.
4. Open **Authentication** and add a **Mobile and desktop applications** platform.
5. Add the exact redirect URI displayed in Home Assistant's Application Credentials description. Home Assistant normally uses the My Home Assistant OAuth redirect when that component is loaded; use the exact value shown by your instance.
6. Use the public-client authorization-code flow with PKCE. Do not create or use a client secret for this integration.

Microsoft requires redirect URIs to match the registered URI exactly. The platform type and redirect behavior still need end-to-end validation with a real personal Microsoft account before this project can be considered release-ready.

## 2. Add the delegated Graph permission

Under **API permissions**, add Microsoft Graph **Delegated permissions**:

- `Mail.ReadBasic` for metadata-only mode (the default and recommended choice).
- `Mail.Read` only if you intend to use optional short-summary mode.

The integration requests only the permission associated with the mode selected in Home Assistant. Metadata-only requests do not select message body or preview fields. Short-summary mode fetches message text locally and stores only the extracted short summary.

Do not add application permissions, `Mail.ReadWrite`, or `Mail.Send`. The integration does not need mail write or send access.

## 3. Add the credentials in Home Assistant

1. Open **Settings → Devices & services**.
2. Open the three-dot menu and choose **Application credentials**.
3. Add credentials for **ParentSquare Email Notifications**.
4. Enter the Application (client) ID from the app registration.
5. Leave the client secret blank.
6. Save, then add **ParentSquare Email Notifications** from the Integrations page.
7. Choose metadata-only or short-summary mode before Microsoft authorization.

Home Assistant manages the OAuth token and refresh lifecycle. Never paste the token into YAML or a GitHub issue.

## 4. Choose the Outlook folder and matching rules

After the account is linked, open the integration's **Configure** / options screen:

- Select the folder that receives ParentSquare notification emails.
- Confirm or change the allowed sender domains. The initial default is `parentsquare.com`; use the actual sender domain shown in a delivered ParentSquare email if it differs.
- Optionally add child matching rules, one per line:

```text
Child label: keyword one, keyword two
Another child: keyword three, keyword four
```

Use distinctive terms that appear in the subject (metadata-only mode) or in the subject / locally extracted short summary (short-summary mode). A notification is assigned only when exactly one child rule matches. Ambiguous matches remain unassigned.

A folder selection and sender-domain allow-list are application-level filters. They do not narrow Microsoft's underlying OAuth permission and a sender-domain match is not cryptographic sender authentication.

## Current limitations

- The Microsoft connection and polling code have synthetic tests but have not yet been validated against a live mailbox.
- The initial polling window is bounded (up to 100 recent messages); the unread sensor reports the retained tracked window, not an authoritative unread total for the entire mailbox.
- Only root-level Outlook folders are currently listed.
- One Microsoft mailbox is supported per Home Assistant instance.
- Other providers are architecture targets, not implemented providers yet.
