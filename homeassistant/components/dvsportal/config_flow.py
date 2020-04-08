"""Config flow for DVSPortal integration."""
import logging

from dvsportal import DVSPortal, DVSPortalAuthError, DVSPortalConnectionError
import voluptuous as vol

from homeassistant import config_entries, exceptions

from .const import CONF_API_HOST, CONF_IDENTIFIER, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({CONF_API_HOST: str, CONF_IDENTIFIER: str, CONF_PASSWORD: str})


async def validate_input(data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    dvsportal = DVSPortal(
        api_host=data[CONF_API_HOST],
        identifier=data[CONF_IDENTIFIER],
        password=data[CONF_PASSWORD],
    )

    try:
        await dvsportal.token()
    except DVSPortalAuthError:
        raise InvalidAuth
    except DVSPortalConnectionError:
        raise CannotConnect

    return {"title": data[CONF_IDENTIFIER]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DVSPortal."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
