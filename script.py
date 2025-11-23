import requests

# --------------------------
# Configuration
# --------------------------
STATE_ID = 2  # Tehran
STATIONS_URL = f"https://aqms.doe.ir/Service/api/v2/Station/GetStationsByStateId/?StateId={STATE_ID}"
AQI_URL = f"https://aqms.doe.ir/Service/api/v2/AQI/Get/?StateId={STATE_ID}"
REGIONS_URL = f"https://aqms.doe.ir/Service/api/v1/Region/Get/?StateId={STATE_ID}"

LOGIN_URL = "https://aqms.doe.ir/Service/v1/login/"

HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "pragma": "no-cache",
    "referer": "https://aqms.doe.ir/App/",
}

# --------------------------
# Bearer token generation
# --------------------------
def generate_bearer_token():
    """
    Generate a fresh bearer token for this execution.
    """
    payload = {
        "grant_type": "password",
        "username": "doeWebAppUser",
        "password": "doeW3bAppU$er"
    }
    headers = {"accept": "application/json", "content-type": "application/x-www-form-urlencoded"}
    resp = requests.post(LOGIN_URL, data=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise Exception("Failed to generate bearer token")
    return token

# --------------------------
# Helper functions
# --------------------------
def fetch_json(url):
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()

def build_station_map(stations_data):
    mapping = {}
    for st in stations_data:
        mapping[st["stationId"]] = {
            "name_en": st.get("stationName_En"),
            "name_fa": st.get("stationName_Fa"),
            "regionId": st.get("regionId")
        }
    return mapping

def build_region_map(regions_data):
    mapping = {}
    for r in regions_data:
        mapping[r["regionId"]] = {
            "name_en": r["regionName_En"],
            "name_fa": r["regionName_Fa"]
        }
    return mapping

def enrich_aqi_data(aqi_records, station_map, region_map):
    enriched = []
    for rec in aqi_records:
        sid = rec.get("stationId")
        rid = rec.get("regionId")
        station_info = station_map.get(sid, {})
        region_info = region_map.get(rid, {})
        rec["stationName_En"] = station_info.get("name_en")
        rec["stationName_Fa"] = station_info.get("name_fa")
        rec["regionName_En"] = region_info.get("name_en")
        rec["regionName_Fa"] = region_info.get("name_fa")
        enriched.append(rec)
    return enriched

def calculate_tehran_avg_aqi(enriched_data):
    tehran_stations = [rec for rec in enriched_data if rec.get("regionId") == 2]
    aqi_values = [rec["aqi"] for rec in tehran_stations if rec.get("aqi") is not None]
    if not aqi_values:
        return None
    return sum(aqi_values) / len(aqi_values)

# --------------------------
# Main script
# --------------------------
def main():
    # Generate fresh token
    token = generate_bearer_token()
    HEADERS["authorization"] = f"Bearer {token}"  # Replace static token with fresh one

    stations_data = fetch_json(STATIONS_URL)
    regions_data = fetch_json(REGIONS_URL)
    aqi_data = fetch_json(AQI_URL)

    station_map = build_station_map(stations_data)
    region_map = build_region_map(regions_data)
    enriched = enrich_aqi_data(aqi_data, station_map, region_map)

    # Print each station's AQI
    for rec in enriched:
        print(f"{rec.get('stationName_En','-')} ({rec.get('stationName_Fa','-')}), "
              f"Region: {rec.get('regionName_En','-')}, AQI: {rec.get('aqi')}")

    # Tehran average
    tehran_avg = calculate_tehran_avg_aqi(enriched)
    if tehran_avg is not None:
        print(f"\n🌆 Tehran average AQI: {tehran_avg:.1f}")
    else:
        print("\nNo AQI data for Tehran.")


if __name__ == "__main__":
    main()
