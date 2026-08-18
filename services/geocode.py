import requests
from urllib.parse import urlencode

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def geocode_address(address, api_key=None, timeout=8):
    """Return (lat, lon) tuple for given address or None if not found.
    If api_key is provided, use Google Geocoding API, otherwise use Nominatim (OpenStreetMap).
    """
    if not address:
        return None
    if api_key:
        params = {"address": address, "key": api_key}
        try:
            r = requests.get(GOOGLE_GEOCODE_URL, params=params, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "OK":
                loc = data["results"][0]["geometry"]["location"]
                return (float(loc["lat"]), float(loc["lng"]))
            return None
        except Exception:
            return None
    # fallback to Nominatim
    params = {"format": "json", "q": address, "limit": 1}
    headers = {"User-Agent": "LocalIA/1.0 (your@email)"}
    try:
        r = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return (lat, lon)
    except Exception:
        return None
