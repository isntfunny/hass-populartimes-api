"""Switch platform for Popular Times."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PopularTimesCoordinator
from .entity import make_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Popular Times switch entities from a config entry."""
    coordinator: PopularTimesCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get("name", entry.title)

    async_add_entities([PopularTimesPollingSwitch(coordinator, entry, name)])


class PopularTimesPollingSwitch(CoordinatorEntity[PopularTimesCoordinator], SwitchEntity):
    """Switch that controls automatic polling."""

    _attr_has_entity_name = True
    _attr_translation_key = "automatic_polling"

    def __init__(
        self,
        coordinator: PopularTimesCoordinator,
        entry: ConfigEntry,
        base_name: str,
    ) -> None:
        """Initialize the polling switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_automatic_polling"
        self._attr_icon = "mdi:sync"
        self._attr_device_info = make_device_info(entry, base_name)

    @property
    def is_on(self) -> bool:
        """Return whether automatic polling is enabled."""
        return self.coordinator.polling_enabled

    @property
    def extra_state_attributes(self) -> dict:
        """Return polling metadata."""
        return {
            "last_poll_source": self.coordinator.last_poll_source,
            "last_poll_at": self.coordinator.last_poll_at,
            "last_update_success": self.coordinator.last_update_success,
            "last_poll_error": self.coordinator.last_poll_error,
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Enable automatic polling."""
        self.coordinator.set_polling_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable automatic polling."""
        self.coordinator.set_polling_enabled(False)
