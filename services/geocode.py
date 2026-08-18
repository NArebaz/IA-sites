from typing import Optional, Tuple

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def geocode_address(address: str, api_key: Optional[str] = None, timeout: int = 8) -> Optional[Tuple[float, float]]:
    """Return (lat, lon) tuple for given address or None if not found.
    If api_key is provided, use Google Geocoding API, otherwise use Nominatim (OpenStreetMap).
    """
    if not address:
        return None
    if api_key:
        try:
            r = requests.get(GOOGLE_GEOCODE_URL, params={"address": address, "key": api_key}, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "OK" and data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                return float(loc["lat"]), float(loc["lng"])
            return None
        except Exception:
            return None
    # fallback to Nominatim
    try:
        headers = {"User-Agent": "LocalIA/1.0 (contact@yourdomain.com)"}
        r = requests.get(NOMINATIM_URL, params={"format": "json", "q": address, "limit": 1}, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None
