"""The DVSPortal integration."""
import asyncio
from datetime import timedelta
import logging

import async_timeout
from dvsportal import DVSPortal
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_API_HOST, CONF_IDENTIFIER, CONF_PASSWORD, DOMAIN

SCAN_INTERVAL = timedelta(seconds=300)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the DVSPortal component."""
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up DVSPortal from a config entry."""

    dvsportal = DVSPortal(
        api_host=entry.data[CONF_API_HOST],
        identifier=entry.data[CONF_IDENTIFIER],
        password=entry.data[CONF_PASSWORD],
    )

    async def async_update_data():
        """Fetch data from API endpoint."""
        async with async_timeout.timeout(10):
            await dvsportal.update()
            return await dvsportal.permits()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="DVSPortal",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
