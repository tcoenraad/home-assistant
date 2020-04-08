"""Support for DVSPortal sensors."""

from datetime import datetime
import logging

from homeassistant.helpers import entity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up DVSPortal sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        DVSPortalSensor(coordinator, idx) for idx, ent in enumerate(coordinator.data)
    )


class DVSPortalSensor(entity.Entity):
    """Defines a DVSPortal sensor."""

    def __init__(self, coordinator, idx):
        """Initialize the DVSPortal entity."""
        self.coordinator = coordinator
        self.idx = idx

    def _permit(self):
        return self.coordinator.data[self.idx]

    def _reservation(self):
        reservations = self._permit()["reservations"]
        if len(reservations) > 0:
            return reservations[0]

    @property
    def name(self):
        """Return entity name."""
        return (
            f"Parking Permit {self._permit()['code']} ({self._permit()['zone_code']})"
        )

    @property
    def state(self):
        """Return entity state."""
        if self._reservation():
            return self._reservation()["license_plate"]

    @property
    def device_state_attributes(self):
        """Return entity state attributes."""
        if self._reservation():
            return {
                "type_id": self._permit()['type_id'],
                "code": self._permit()['code'],
                "zone_code": self._permit()['zone_code'],
                "reservation_id": self._reservation()["id"],
                "reservation_valid_from": datetime.fromisoformat(self._reservation()["valid_from"]),
                "reservation_valid_until": datetime.fromisoformat(
                    self._reservation()["valid_until"]
                ),
                "reservation_license_plate_name": self._permit()["license_plates"].get(
                    self._reservation()["license_plate"]
                ),
            }

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return f"{DOMAIN}_{self._permit()['code']}_{self._permit()['zone_code']}"

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self.coordinator.async_request_refresh()
