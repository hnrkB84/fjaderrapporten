import requests
import json
import os
from datetime import datetime
from urllib.parse import urlencode

# === KONFIGURATION ===
API_KEY = os.getenv("Ocp_Apim_Subscription_Key")
API_URL_BASE = "https://api.artdatabanken.se/species-observation-system/v1/Observations/Search"

headers = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json",
    "X-Api-Version": "1.5"
}

payload = {
    "taxon": {
        "ids": [4000104],
        "includeUnderlyingTaxa": True
    },
    "geographics": {
        "areas": [
            {
                "areaType": "Municipality",
                "featureId": "686"
            }
        ],
        "considerDisturbanceRadius": False,
        "considerObservationAccuracy": False
    },
    "date": {
        "startDate": "2024-01-01",
        "endDate": "2025-12-31",
        "dateFilterType": "BetweenStartDateAndEndDate"
    },
    "output": {
        "fields": [
            "event.startDate",
            "location.name",
            "taxon.vernacularName",
            "taxon.scientificName",
            "reportedBy.fullName",
            "event.activity",
            "event.individualCount"
        ]
    }
}

# === ANROP ===
def hamta_fagelfynd():
    print("⏳ Hämtar fågelfynd från Artportalen...")

    query_params = {
        "skip": 0,
        "take": 500,
        "sortBy": "event.startDate",
        "sortOrder": "Desc"
    }
    full_url = f"{API_URL_BASE}?{urlencode(query_params)}"

    try:
        response = requests.post(full_url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"🚨 Fel vid API-anrop: {e}")
        return

    print("✅ API-svar mottaget")
    data = response.json()
    observationer = []

    for record in data.get("records", []):
        art = record.get("taxon", {}).get("vernacularName", "okänd art")
        scientific_name = record.get("taxon", {}).get("scientificName", "okänt namn")
        datum_str = record.get("event", {}).get("startDate")
        lokal = record.get("location", {}).get("name") or "Eksjö"
        antal = record.get("event", {}).get("individualCount", 1)

        if datum_str and datum_str >= "2025-04-01":
            observationer.append({
                "art": art,
                "scientificName": scientific_name,
                "datum": datum_str,
                "lokal": lokal,
                "antal": antal
            })

    senaste_15 = observationer[:15]

    with open("data/eksjo_faglar_apiresponse.json", "w", encoding="utf-8") as f:
        json.dump(senaste_15, f, ensure_ascii=False, indent=2)

    print(f"📝 Sparade {len(senaste_15)} fynd till data/eksjo_faglar_apiresponse.json")

# === KÖR ===
if __name__ == "__main__":
    if not API_KEY:
        print("❌ API-nyckel saknas! Lägg till Ocp_Apim_Subscription_Key som GitHub secret.")
    else:
        hamta_fagelfynd()
# Din riktiga scriptkod ska in här
