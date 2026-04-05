"""Button platform for Popular Times."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Set up Popular Times button entities from a config entry."""
    coordinator: PopularTimesCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get("name", entry.title)

    async_add_entities([PopularTimesRefreshButton(coordinator, entry, name)])


class PopularTimesRefreshButton(CoordinatorEntity[PopularTimesCoordinator], ButtonEntity):
    """Button that triggers a manual refresh."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh"

    def __init__(
        self,
        coordinator: PopularTimesCoordinator,
        entry: ConfigEntry,
        base_name: str,
    ) -> None:
        """Initialize the refresh button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_icon = "mdi:refresh"
        self._attr_device_info = make_device_info(entry, base_name)

    async def async_press(self) -> None:
        """Run a manual coordinator refresh."""
        await self.coordinator.async_manual_refresh()
