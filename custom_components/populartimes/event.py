"""Event platform for Popular Times."""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PopularTimesCoordinator
from .entity import make_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Popular Times event entities from a config entry."""
    coordinator: PopularTimesCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get("name", entry.title)

    async_add_entities([PopularTimesPollEventEntity(coordinator, entry, name)])


class PopularTimesPollEventEntity(EventEntity):
    """Event entity that emits scraper success and failure events."""

    _attr_has_entity_name = True
    _attr_translation_key = "poll_event"
    _attr_event_types = [
        "automatic_poll_completed",
        "manual_poll_completed",
        "automatic_poll_failed",
        "manual_poll_failed",
    ]

    def __init__(
        self,
        coordinator: PopularTimesCoordinator,
        entry: ConfigEntry,
        base_name: str,
    ) -> None:
        """Initialize the poll event entity."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_poll_event"
        self._attr_icon = "mdi:calendar-refresh"
        self._attr_device_info = make_device_info(entry, base_name)

    async def async_added_to_hass(self) -> None:
        """Register coordinator listeners when added to Home Assistant."""
        await super().async_added_to_hass()
        self.coordinator.add_poll_success_listener(self._handle_poll_success)
        self.coordinator.add_poll_error_listener(self._handle_poll_error)
        self.async_on_remove(
            lambda: self.coordinator.remove_poll_success_listener(self._handle_poll_success)
        )
        self.async_on_remove(
            lambda: self.coordinator.remove_poll_error_listener(self._handle_poll_error)
        )

    def _handle_poll_success(self, source: str, payload: dict[str, Any]) -> None:
        """Emit an entity event after a successful poll."""
        live = payload.get("live", {})
        opening = payload.get("opening", {})
        self._trigger_event(
            self._success_event_type(source),
            {
                "name": payload.get("name"),
                "address": payload.get("address"),
                "maps_url": payload.get("maps_url"),
                "popularity_is_live": live.get("is_live", False),
                "current_pct": live.get("current_pct"),
                "usual_pct": live.get("usual_pct"),
                "is_open": opening.get("is_open"),
                "status_text": opening.get("status_text"),
            },
        )
        self.async_write_ha_state()

    def _handle_poll_error(self, source: str, message: str, err: Exception) -> None:
        """Emit an entity event after a failed poll."""
        self._trigger_event(
            self._error_event_type(source),
            {
                "address": self.coordinator.address,
                "error": message,
                "error_type": type(err).__name__,
            },
        )
        self.async_write_ha_state()

    @staticmethod
    def _success_event_type(source: str) -> str:
        """Map the poll source to a success event type."""
        return "manual_poll_completed" if source == "manual" else "automatic_poll_completed"

    @staticmethod
    def _error_event_type(source: str) -> str:
        """Map the poll source to an error event type."""
        return "manual_poll_failed" if source == "manual" else "automatic_poll_failed"
