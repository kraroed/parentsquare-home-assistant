"""Microsoft consumer OAuth application credentials."""

from homeassistant.components.application_credentials import (
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    AbstractOAuth2Implementation,
    LocalOAuth2ImplementationWithPkce,
)

AUTHORIZE_URL = (
    "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
)
TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
APP_REGISTRATION_URL = (
    "https://entra.microsoft.com/#view/"
    "Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
)


async def async_get_authorization_server(
    hass: HomeAssistant,
) -> AuthorizationServer:
    """Return the Microsoft consumer authorization server."""
    return AuthorizationServer(
        authorize_url=AUTHORIZE_URL,
        token_url=TOKEN_URL,
    )


async def async_get_auth_implementation(
    hass: HomeAssistant,
    auth_domain: str,
    credential: ClientCredential,
) -> AbstractOAuth2Implementation:
    """Use authorization code with PKCE as a public client."""
    return LocalOAuth2ImplementationWithPkce(
        hass,
        auth_domain,
        credential.client_id,
        authorize_url=AUTHORIZE_URL,
        token_url=TOKEN_URL,
        client_secret=credential.client_secret,
    )


async def async_get_description_placeholders(
    hass: HomeAssistant,
) -> dict[str, str]:
    """Return the Microsoft app registration link."""
    return {"console_url": APP_REGISTRATION_URL}
