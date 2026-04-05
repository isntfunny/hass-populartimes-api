"""Shared entity helpers for Popular Times."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


def make_device_info(entry: ConfigEntry, base_name: str) -> DeviceInfo:
    """Build shared DeviceInfo for all entities in a config entry."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=base_name,
        entry_type=DeviceEntryType.SERVICE,
        manufacturer="Google Maps",
        configuration_url=entry.data.get("maps_url"),
    )
