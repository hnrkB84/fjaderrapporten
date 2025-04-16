import requests
import json
from datetime import datetime
from urllib.parse import urlencode
from pathlib import Path
import os

# 🔐 API-nyckel från miljövariabel
API_KEY = os.getenv("OCP_APIM_SUBSCRIPTION_KEY")

API_URL_BASE = "https://api.artdatabanken.se/species-observation-system/v1/Observations/Search"

headers = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json",
    "X-Api-Version": "1.5"
}

payload = {
    "taxon": {
        "ids": [4000104],  # Alla fåglar
        "includeUnderlyingTaxa": True
    },
    "geographics": {
        "areas": [
            {
                "areaType": "Municipality",
                "featureId": "686"  # Eksjö
            }
        ],
        "considerDisturbanceRadius": False,
        "considerObservationAccuracy": False
    },
    "date": {
        "startDate": "2025-01-01",
        "endDate": datetime.now().strftime("%Y-%m-%d"),
        "dateFilterType": "BetweenStartDateAndEndDate"
    },
    "output": {
        "fields": [
            "event.startDate",
            "location.locality",
            "taxon.vernacularName",
            "taxon.scientificName"
        ]
    }
}

def skapa_checklista():
    print("📋 Skapar checklista från Artportalen...")

    query_params = {
        "skip": 0,
        "take": 2000,
        "sortBy": "event.startDate",
        "sortOrder": "Asc"
    }
    full_url = f"{API_URL_BASE}?{urlencode(query_params)}"

    try:
        response = requests.post(full_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Fel vid hämtning: {e}")
        return

    data = response.json()
    arter = {}

    for record in data.get("records", []):
        art = record.get("taxon", {}).get("vernacularName")
        art_lat = record.get("taxon", {}).get("scientificName")
        datum = record.get("event", {}).get("startDate")
        plats = record.get("location", {}).get("locality")

        if art_lat not in arter:
            arter[art_lat] = {
                "art": art,
                "scientificName": art_lat,
                "förstSedd": datum,
                "lokal": plats or "okänd plats"
            }

    # Sortera efter artnamn
    checklista = list(arter.values())
    checklista.sort(key=lambda x: x["art"])

    with open("data/checklista.json", "w", encoding="utf-8") as f:
        json.dump(checklista, f, ensure_ascii=False, indent=2)

    print(f"✅ Sparade {len(checklista)} unika arter till data/checklista.json")

if __name__ == "__main__":
    skapa_checklista()
