import requests
import json
from datetime import datetime
from urllib.parse import urlencode, quote_plus  # ✅ Lägg till quote_plus
from pathlib import Path
import sys
import os

API_KEY = os.getenv("OCP_APIM_SUBSCRIPTION_KEY")
API_URL_BASE = "https://api.artdatabanken.se/species-observation-system/v1/Observations/Search"

headers = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json",
    "X-Api-Version": "1.5"
}

artbilder_override_path = Path("data/artbilder_override.json")
artbilder_auto_path = Path("data/artbilder_auto.json")

if artbilder_auto_path.exists():
    with open(artbilder_auto_path, encoding="utf-8") as f:
        ARTBILDER_AUTO = json.load(f)
else:
    ARTBILDER_AUTO = {}

if artbilder_override_path.exists():
    with open(artbilder_override_path, encoding="utf-8") as f:
        ARTBILDER_OVERRIDE = json.load(f)
else:
    ARTBILDER_OVERRIDE = {}

def hitta_override(namn):
    namn = namn.lower().strip()
    for key in ARTBILDER_OVERRIDE:
        if key.lower().strip() == namn:
            return ARTBILDER_OVERRIDE[key]
    return None

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
            "location.locality",
            "location.municipality.name",
            "taxon.vernacularName",
            "taxon.scientificName",
            "recordedBy",
            "event.individualCount",
            "event.activity"
        ]
    }
}

def hamta_fagelfynd():
    print("📡 Hämtar fågelfynd från Artportalen...")

    query_params = {
        "skip": 0,
        "take": 50,
        "sortBy": "event.startDate",
        "sortOrder": "Desc"
    }
    full_url = f"{API_URL_BASE}?{urlencode(query_params)}"

    try:
        response = requests.post(full_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Fel vid hämtning: {e}")
        sys.exit(1)

    print("✅ API-svar mottaget")
    try:
        data = response.json()
        observationer = []

        for record in data.get("records", []):
            art = record.get("taxon", {}).get("vernacularName", "Okänd art")
            scientific_name = record.get("taxon", {}).get("scientificName", "Okänt namn").strip()
            observation_date_str = record.get("event", {}).get("startDate", None)
            locality = record.get("location", {}).get("locality", "")
            municipality = record.get("location", {}).get("municipality", {}).get("name", "okänd kommun")
            plats = locality or municipality
            observator = record.get("recordedBy", "okänd observatör")
            antal = record.get("event", {}).get("individualCount", 1)
            aktivitet = record.get("event", {}).get("activity", "okänd")

            # 🔁 Prioritera override > auto
            override = hitta_override(scientific_name)
            auto = ARTBILDER_AUTO.get(scientific_name)

            bild = override.get("bild") if override else auto.get("bild") if auto else None
            bild_lank = override.get("bild_lank") if override else auto.get("bild_lank") if auto else None

            # 🌍 Bygg Google Maps-länk
            platsnamn = plats
            sokfras = f"{platsnamn}, Eksjö, Sverige"
            google_maps_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(sokfras)}"

            if override:
                print(f"📸 Override används för {scientific_name}")

            if observation_date_str:
                try:
                    observation_date = datetime.fromisoformat(observation_date_str)
                    formatted_date = observation_date.isoformat()
                except ValueError:
                    formatted_date = observation_date_str

                observationer.append({
                    "art": art,
                    "scientificName": scientific_name,
                    "datum": formatted_date,
                    "lokal": plats,
                    "rapporteradAv": observator,
                    "antal": antal,
                    "observationstyp": aktivitet,
                    "bild": bild,
                    "bild_lank": bild_lank,
                    "googleMapsLank": google_maps_url  # ✅ Nytt fält!
                })

        if observationer:
            with open("data/eksjo_faglar_apiresponse.json", "w", encoding="utf-8") as f:
                json.dump(observationer, f, ensure_ascii=False, indent=2)
            print(f"💾 Sparade {len(observationer)} fynd till data/eksjo_faglar_apiresponse.json")
        else:
            print("⚠️ Inga observationer sparade – listan är tom.")

    except Exception as e:
        print(f"❌ Fel vid hantering av data: {e}")

if __name__ == "__main__":
    hamta_fagelfynd()
