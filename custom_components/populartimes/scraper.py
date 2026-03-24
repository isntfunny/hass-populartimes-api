"""Playwright CDP scraper for Google Maps popular times data."""

import logging
import re
import urllib.parse
from datetime import datetime

from playwright.async_api import async_playwright

from .const import DAYS_EN

_LOGGER = logging.getLogger(__name__)

# Regex patterns for German and English aria-labels
RE_LIVE_DE = re.compile(
    r"Derzeit zu (\d+)\s*% ausgelastet;?\s*normal sind (\d+)\s*%"
)
RE_LIVE_EN = re.compile(
    r"Currently (\d+)\s*% busy.*?usually (\d+)\s*%"
)
RE_HOURLY_DE = re.compile(
    r"Um (\d+) Uhr zu (\d+)\s*% ausgelastet"
)
RE_HOURLY_EN = re.compile(
    r"(\d+)% busy at (\d+)\s*(am|pm)"
)

class ScraperError(Exception):
    """Base exception for scraper errors."""


class ConnectionFailed(ScraperError):
    """Could not connect to CDP browser."""


def _parse_labels(labels: list[str]) -> dict:
    """Parse aria-label strings into structured popular times data."""
    times: list[list[int]] = [[0] * 24 for _ in range(7)]
    current_day = 0
    live_pct = None
    usual_pct = None

    # Track which hours we've seen in the current day to detect day boundaries
    seen_hours: set[int] = set()

    for label in labels:
        # Live data (German)
        m = RE_LIVE_DE.search(label)
        if m:
            live_pct = int(m.group(1))
            usual_pct = int(m.group(2))
            continue

        # Live data (English)
        m = RE_LIVE_EN.search(label)
        if m:
            live_pct = int(m.group(1))
            usual_pct = int(m.group(2))
            continue

        # Hourly data (German)
        m = RE_HOURLY_DE.search(label)
        if m:
            hour = int(m.group(1))
            pct = int(m.group(2))

            if hour in seen_hours:
                current_day += 1
                seen_hours = set()

            seen_hours.add(hour)
            if current_day < 7:
                times[current_day][hour] = pct
            continue

        # Hourly data (English)
        m = RE_HOURLY_EN.search(label)
        if m:
            pct = int(m.group(1))
            raw_hour = int(m.group(2))
            ampm = m.group(3)
            hour = raw_hour % 12 if ampm == "am" else (raw_hour % 12) + 12

            if hour in seen_hours:
                current_day += 1
                seen_hours = set()

            seen_hours.add(hour)
            if current_day < 7:
                times[current_day][hour] = pct
            continue

    # Map day indices to weekday names starting from today
    today_idx = datetime.now().weekday()  # 0=Monday
    popular_times = {}
    for i in range(7):
        day_name = DAYS_EN[(today_idx + i) % 7]
        popular_times[day_name] = times[i]

    return {
        "live": {
            "current_pct": live_pct,
            "usual_pct": usual_pct,
            "is_live": live_pct is not None,
        },
        "popular_times": popular_times,
    }


async def scrape_popular_times(cdp_url: str, address: str) -> dict:
    """Scrape Google Maps for popular times data via Playwright CDP.

    Returns dict with keys: name, address, maps_url, live, popular_times.
    Raises ConnectionFailed or NoDataFound on failure.
    """
    labels: list[str] = []

    try:
        pw = await async_playwright().start()
    except Exception as err:
        raise ConnectionFailed(f"Failed to start Playwright: {err}") from err

    try:
        try:
            browser = await pw.chromium.connect_over_cdp(cdp_url, timeout=10000)
        except Exception as err:
            raise ConnectionFailed(
                f"Failed to connect to CDP at {cdp_url}: {err}"
            ) from err

        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await context.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})

        # Navigate to Google Maps search
        search_url = (
            "https://www.google.com/maps/search/"
            + urllib.parse.quote_plus(address)
        )
        _LOGGER.debug("Navigating to %s", search_url)
        await page.goto(search_url, timeout=30000)
        await page.wait_for_timeout(2000)

        # Handle cookie consent (German or English)
        for consent_text in ["Alle akzeptieren", "Accept all"]:
            try:
                btn = page.locator(f"button:has-text('{consent_text}')").first
                if await btn.is_visible(timeout=3000):
                    await btn.click()
                    await page.wait_for_timeout(3000)
                    break
            except Exception:
                continue

        # Wait for page to settle
        await page.wait_for_timeout(3000)

        # If we landed on a search results list, click the first result
        try:
            first_result = page.locator("a[href*='/maps/place/']").first
            if await first_result.is_visible(timeout=3000):
                await first_result.click()
                # Wait until h1 changes from "Ergebnisse"/"Results"
                try:
                    await page.wait_for_function(
                        """() => {
                            const h1 = document.querySelector('h1');
                            return h1 && h1.textContent &&
                                   h1.textContent !== 'Ergebnisse' &&
                                   h1.textContent !== 'Results';
                        }""",
                        timeout=10000,
                    )
                except Exception:
                    pass
                await page.wait_for_timeout(3000)
        except Exception:
            pass

        # Wait for place details to load
        await page.wait_for_timeout(2000)

        # Extract place name — find the h1 that isn't "Ergebnisse"/"Results"/empty
        place_name = await page.evaluate("""() => {
            const all = document.querySelectorAll('h1');
            for (const h of all) {
                const t = (h.textContent || '').trim();
                if (t && t !== 'Ergebnisse' && t !== 'Results') return t;
            }
            return null;
        }""")

        # Get current URL (resolved Maps URL)
        maps_url = page.url

        # Extract address from the page
        resolved_address = await page.evaluate("""() => {
            const btns = document.querySelectorAll('button[aria-label]');
            for (const btn of btns) {
                const label = btn.getAttribute('aria-label') || '';
                if (label.startsWith('Adresse:') || label.startsWith('Address:')) {
                    return label.replace('Adresse: ', '').replace('Address: ', '').trim();
                }
            }
            return null;
        }""")

        # Extract all busyness aria-labels
        labels = await page.evaluate("""() => {
            const els = document.querySelectorAll('[aria-label]');
            const out = [];
            for (const el of els) {
                const l = el.getAttribute('aria-label');
                if (l && (l.includes('ausgelastet') || l.includes('busy') ||
                          l.includes('Derzeit') || l.includes('Currently')))
                    out.push(l);
            }
            return out;
        }""")

        await page.close()

    finally:
        await pw.stop()

    parsed = _parse_labels(labels)

    return {
        "name": place_name,
        "address": resolved_address or address,
        "maps_url": maps_url,
        "live": parsed["live"],
        "popular_times": parsed["popular_times"],
    }
