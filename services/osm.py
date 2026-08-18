from typing import Dict, List, Optional, Tuple

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _safe_post(query: str, timeout: int = 30) -> Optional[Dict]:
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def find_businesses_osm(lat: float, lon: float, radius: int = 1000) -> List[Dict]:
    query = f"""
    [out:json][timeout:25];
    (
      node(around:{radius},{lat},{lon})[shop];
      way(around:{radius},{lat},{lon})[shop];
      node(around:{radius},{lat},{lon})[amenity~"restaurant|cafe|bar|fast_food|clinic|bank|pharmacy|hospital|barbershop|beauty_salon"];
      way(around:{radius},{lat},{lon})[amenity~"restaurant|cafe|bar|fast_food|clinic|bank|pharmacy|hospital|barbershop|beauty_salon"];
    );
    out center tags;
    """
    data = _safe_post(query)
    if not data:
        return []
    results: List[Dict] = []
    for el in data.get("elements", []):
        tags = el.get("tags", {}) or {}
        name = tags.get("name")
        if not name:
            continue
        address = ", ".join(filter(None, [
            tags.get("addr:street"),
            tags.get("addr:housenumber"),
            tags.get("addr:city"),
            tags.get("addr:postcode"),
        ]))
        results.append({
            "id": el.get("id"),
            "name": name,
            "address": address,
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "email": tags.get("email") or tags.get("contact:email"),
            "website": tags.get("website") or tags.get("contact:website"),
            "raw_tags": tags,
        })
    return results
