import requests
import json
from datetime import datetime
from urllib.parse import urlencode
from pathlib import Path

API_KEY = "38fd64de3bcb43628a457153476e476b"
API_URL_BASE = "https://api.artdatabanken.se/species-observation-system/v1/Observations/Search"

headers = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json",
    "X-Api-Version": "1.5"
}

# Läs in ARTBILDER från fil som skapats av bygg_artbilder_auto.py
artbilder_path = Path("data/artbilder_auto.json")
if artbilder_path.exists():
    with open(artbilder_path, encoding="utf-8") as f:
        ARTBILDER = json.load(f)
else:
    ARTBILDER = {}

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
        response = requests.post(full_url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Fel vid hämtning: {e}")
        return

    print("✅ API-svar mottaget")
    try:
        data = response.json()
        observationer = []

        for record in data.get("records", []):
            art = record.get("taxon", {}).get("vernacularName", "Okänd art")
            scientific_name = record.get("taxon", {}).get("scientificName", "Okänt namn")
            observation_date_str = record.get("event", {}).get("startDate", None)
            locality = record.get("location", {}).get("locality", "")
            municipality = record.get("location", {}).get("municipality", {}).get("name", "okänd kommun")
            plats = locality or municipality
            observator = record.get("recordedBy", "okänd observatör")
            antal = record.get("event", {}).get("individualCount", 1)
            aktivitet = record.get("event", {}).get("activity", "okänd")

            # Hämta bild från ARTBILDER baserat på vetenskapligt namn
            bildinfo = ARTBILDER.get(scientific_name, {})
            bild = bildinfo.get("bild")
            bild_lank = bildinfo.get("bild_lank")

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
                    "bild_lank": bild_lank
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
