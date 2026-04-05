# hass-populartimes
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

## Description
Custom component for Home Assistant that shows the current popularity for any place found on Google Maps. Data is scraped directly from Google Maps via a headless Chrome browser using the Chrome DevTools Protocol (CDP).

Sensor attributes include hourly popularity data for each day of the week.

> **Important:** This integration requires a running stealth CDP browser. See [Prerequisites](#prerequisites) below.

## Prerequisites

### Stealth CDP Browser (required)

This integration connects to a remote Chrome/Chromium browser via CDP to scrape Google Maps. A regular Chromium instance will get blocked by Google — **you need a stealth browser** that avoids bot detection.

Recommended: [CloakBrowser](https://github.com/nickhq/cloak) — a stealth Chromium browser with anti-detection built in.

**Docker Compose example:**

```yaml
services:
  stealth-browser:
    container_name: stealth-browser
    image: cloakhq/cloakbrowser
    restart: unless-stopped
    ports:
      - "9222:9222"
    command: cloakserve
```

The browser must be reachable from your Home Assistant instance at the configured CDP URL (default: `http://192.168.178.5:9222`).

Other stealth browsers that expose a CDP endpoint on port 9222 should also work.

## Installation

1. Install via [HACS](https://hacs.xyz/) (recommended), or
2. Download this repo and copy the `custom_components/populartimes` folder into your Home Assistant `custom_components` directory.

## Configuration

Add the integration via **Settings > Devices & Services > Add Integration > Popular Times**.

You will be asked for:
- **Address** — The place to track, preferably in the format: `Location Name, Full Address, City, Country`
- **CDP URL** — The URL of your stealth browser's CDP endpoint (default: `http://192.168.178.5:9222`)

## Sensors

The integration creates multiple entities per configured place:

- sensors for current, usual, and difference popularity
- binary sensors for live data availability and open/closed state
- a refresh button for manual scraping
- a switch to enable or disable automatic polling
- an event entity for successful and failed polls

### Attributes

| Attribute | Description |
|---|---|
| `popularity_is_live` | `true` if Google is reporting real-time data, `false` if using historical averages |
| `live_current_pct` | Current popularity percentage (live) |
| `live_usual_pct` | Usual popularity percentage for this time (live) |
| `place_name` | Resolved place name from Google Maps |
| `address` | Resolved address |
| `maps_url` | Direct Google Maps URL for the place |
| `Monday` .. `Sunday` | List of 24 hourly popularity values (0-100) for each day |

## Live vs historical data

Sometimes Google Maps does not provide live popularity data for a place. In that case, historical data is used to set the sensor state. The attribute `popularity_is_live` indicates which data source is active.

## Extra entities

### Refresh button

Each place gets a `refresh` button entity. Pressing it triggers a scrape immediately, even when automatic polling is disabled.

### Automatic polling switch

Each place gets an `automatic polling` switch entity.

- `on`: the coordinator keeps polling on the configured interval
- `off`: scheduled polling is skipped, but the last known data stays available

### Poll event entity

Each place gets a `poll event` entity with these event types:

- `automatic_poll_completed`
- `manual_poll_completed`
- `automatic_poll_failed`
- `manual_poll_failed`

Successful events include compact scraper output such as place name, address, Maps URL, live popularity values, and open/closed status.

Failed events include the configured address, the error message, and the exception type from the scraper path.

## Links

- [Home Assistant Community Topic](https://community.home-assistant.io/t/google-maps-places-popular-times-component/147362)
