import requests
import time
from typing import Dict, List, Optional

PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def find_businesses_google(lat: float, lon: float, radius: int, api_key: str, max_results: int = 60) -> List[Dict]:
    latlng = f"{lat},{lon}"
    params = {"location": latlng, "radius": radius, "key": api_key}
    out: List[Dict] = []
    next_page = None
    while True:
        if next_page:
            time.sleep(2)
            params = {"pagetoken": next_page, "key": api_key}
        r = requests.get(PLACES_NEARBY_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        for p in data.get("results", []):
            place_id = p.get("place_id")
            name = p.get("name")
            address = p.get("vicinity") or p.get("formatted_address")
            details = {}
            try:
                d = requests.get(
                    PLACES_DETAILS_URL,
                    params={"place_id": place_id, "key": api_key, "fields": "website,formatted_phone_number,name,formatted_address"},
                    timeout=10,
                )
                d.raise_for_status()
                details = d.json().get("result", {})
            except Exception:
                details = {}
            out.append({
                "id": place_id,
                "name": name,
                "address": details.get("formatted_address", address),
                "phone": details.get("formatted_phone_number"),
                "email": details.get("email"),
                "website": details.get("website"),
            })
            if len(out) >= max_results:
                return out
        next_page = data.get("next_page_token")
        if not next_page:
            break
    return out
