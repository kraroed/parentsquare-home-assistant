# ParentSquare for Home Assistant

An independent Home Assistant integration project intended to organize ParentSquare school communications by student.

> **Development status: discovery / authorization required.** This repository does not currently connect to ParentSquare, authenticate, collect messages, or store ParentSquare content.

## Intended capabilities

- One account connection with MFA support where permitted.
- Discover parent-visible students and schools.
- Associate communications with the relevant student, school, sender, and timestamp.
- Maintain a local, deduplicated history and unread counts.
- Expose Home Assistant sensors and events.
- Provide configurable notifications and a family Lovelace card.

## Important access and terms notice

ParentSquare does not publish a parent-facing public API. Third-party projects currently use undocumented interfaces or parse authenticated web pages; these interfaces can change without notice.

The current [ParentSquare Terms of Use](https://www.parentsquare.com/terms/) prohibit copying, reproducing, or sharing content from public or password-protected ParentSquare pages without prior express written consent of the content owner, where such copying violates rights. District-specific agreements and policies may also apply.

**This project will not implement scraping, undocumented endpoint access, message copying, or persistent message storage unless the necessary written authorization is obtained and the permitted scope is clear.** A parent's ability to view a message in the app is not, by itself, evidence that a third-party integration may copy or retain it.

Before enabling a live connector, obtain written clarification from the district and/or ParentSquare covering:
1. Whether an independently operated Home Assistant integration may access the account.
2. Whether messages, announcements, student associations, and attachments may be retrieved.
3. Whether content may be stored locally, for how long, and whether it may be displayed in Home Assistant notifications or dashboards.
4. Whether any official API, export, or approved integration is available.

Until then, development is limited to repository scaffolding, synthetic fixtures, and features that do not access or reproduce protected ParentSquare content.

## Privacy and security goals

- Never commit credentials, MFA codes, cookies, session tokens, real messages, student names, or school identifiers.
- Keep any future credentials and session material in Home Assistant's encrypted config-entry storage.
- Default to read-only behavior.
- Minimize retained content and provide configurable retention/deletion controls if storage is authorized.
- Use synthetic test data only.
- Do not send family communication content to third-party services.

## Planned architecture

1. **Access review:** confirm authorized access method and permitted data scope.
2. **Authentication:** implement account setup and MFA only for an approved access method.
3. **Discovery:** map parent-visible students, schools, and groups.
4. **Data model:** normalize permitted communications and associate them with students.
5. **Storage:** implement local deduplication and retention only within the approved scope.
6. **Entities:** add per-student sensors and integration-wide status entities.
7. **Notifications/card:** add configurable notifications and a separate Lovelace card.
8. **Validation:** run Home Assistant, HACS, lint, and regression tests before releases.

## Development

No live ParentSquare connection is included in this initial project scaffold. Do not enter ParentSquare credentials into Home Assistant for this project yet.

## Disclaimer

This project is independent and is not affiliated with, endorsed by, or sponsored by ParentSquare, Inc. ParentSquare and related marks belong to their respective owners. Use of this project must comply with applicable terms, district policies, privacy requirements, and applicable law.
