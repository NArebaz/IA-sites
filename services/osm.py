import requests
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def find_businesses_osm(lat, lon, radius=1000):
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
    r = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
    r.raise_for_status()
    payload = r.json()
    results = []
    for el in payload.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        address = ", ".join(filter(None, [
            tags.get("addr:street"),
            tags.get("addr:housenumber"),
            tags.get("addr:city"),
            tags.get("addr:postcode")
        ]))
        results.append({
            "id": el.get("id"),
            "name": name,
            "address": address,
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "email": tags.get("email") or tags.get("contact:email"),
            "website": tags.get("website") or tags.get("contact:website"),
            "raw_tags": tags
        })
    return results
