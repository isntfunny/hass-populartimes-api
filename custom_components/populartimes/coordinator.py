"""DataUpdateCoordinator for Popular Times."""

from __future__ import annotations

import logging
from datetime import timedelta
from functools import partial
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DEFAULT_SCAN_INTERVAL
from .scraper import ConnectionFailed, scrape_popular_times

_LOGGER = logging.getLogger(__name__)

PollSuccessListener = Callable[[str, dict[str, Any]], None]
PollErrorListener = Callable[[str, str, Exception], None]


class PopularTimesCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch popular times data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        cdp_url: str,
        address: str,
        scan_interval_min: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="Popular Times",
            update_interval=timedelta(minutes=scan_interval_min),
        )
        self.cdp_url = cdp_url
        self.address = address
        self.polling_enabled = True
        self.last_poll_source: str | None = None
        self.last_poll_at = None
        self.last_update_success = False
        self.last_poll_payload: dict[str, Any] | None = None
        self.last_poll_error: str | None = None
        self._poll_success_listeners: list[PollSuccessListener] = []
        self._poll_error_listeners: list[PollErrorListener] = []

    async def _async_fetch_data(self, source: str) -> dict[str, Any]:
        """Fetch data from Google Maps via pychrome CDP."""
        try:
            data = await self.hass.async_add_executor_job(
                partial(scrape_popular_times, self.cdp_url, self.address)
            )
        except ConnectionFailed as err:
            self._handle_poll_error(source, f"CDP connection failed: {err}", err)
            raise UpdateFailed(f"CDP connection failed: {err}") from err
        except Exception as err:
            self._handle_poll_error(source, f"Error fetching popular times: {err}", err)
            raise UpdateFailed(f"Error fetching popular times: {err}") from err

        self.last_poll_source = source
        self.last_poll_at = dt_util.utcnow()
        self.last_update_success = True
        self.last_poll_payload = data
        self.last_poll_error = None
        self._notify_poll_success(source, data)
        return data

    async def _async_update_data(self) -> dict:
        """Fetch data for scheduled coordinator updates."""
        if not self.polling_enabled:
            return self.data or {}

        return await self._async_fetch_data("auto")

    async def async_manual_refresh(self) -> None:
        """Run a manual refresh even when automatic polling is disabled."""
        data = await self._async_fetch_data("manual")
        self.async_set_updated_data(data)

    def set_polling_enabled(self, enabled: bool) -> None:
        """Enable or disable automatic polling."""
        self.polling_enabled = enabled
        self.async_update_listeners()

    def add_poll_success_listener(self, listener: PollSuccessListener) -> None:
        """Register a listener for successful polls."""
        self._poll_success_listeners.append(listener)

    def remove_poll_success_listener(self, listener: PollSuccessListener) -> None:
        """Remove a successful poll listener."""
        if listener in self._poll_success_listeners:
            self._poll_success_listeners.remove(listener)

    def add_poll_error_listener(self, listener: PollErrorListener) -> None:
        """Register a listener for poll failures."""
        self._poll_error_listeners.append(listener)

    def remove_poll_error_listener(self, listener: PollErrorListener) -> None:
        """Remove a poll failure listener."""
        if listener in self._poll_error_listeners:
            self._poll_error_listeners.remove(listener)

    def _notify_poll_success(self, source: str, payload: dict[str, Any]) -> None:
        """Notify listeners after a successful poll."""
        for listener in tuple(self._poll_success_listeners):
            listener(source, payload)

    def _handle_poll_error(self, source: str, message: str, err: Exception) -> None:
        """Track and notify listeners about polling failures."""
        self.last_poll_source = source
        self.last_poll_at = dt_util.utcnow()
        self.last_update_success = False
        self.last_poll_error = message
        for listener in tuple(self._poll_error_listeners):
            listener(source, message, err)
