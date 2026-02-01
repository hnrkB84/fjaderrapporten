import requests
import json
from datetime import datetime
from pathlib import Path
import os

API_KEY = os.getenv("OCP_APIM_SUBSCRIPTION_KEY")
API_URL_BASE = "https://api.artdatabanken.se/species-observation-system/v1/Observations/Search"

headers = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json",
    "X-Api-Version": "1.5"
}

# Högland — samma kommuner som hamta_faglar.py
KOMMUNER = [
    {"areaType": "Municipality", "featureId": "686"},  # Eksjö
    {"areaType": "Municipality", "featureId": "684"},  # Nässjö
    {"areaType": "Municipality", "featureId": "682"},  # Aneby
    {"areaType": "Municipality", "featureId": "687"},  # Tranås
    {"areaType": "Municipality", "featureId": "688"},  # Vetlanda
]

payload = {
    "taxon": {
        "ids": [4000104],
        "includeUnderlyingTaxa": True
    },
    "geographics": {
        "areas": KOMMUNER,
        "considerDisturbanceRadius": False,
        "considerObservationAccuracy": False
    },
    "date": {
        "startDate": "2015-01-01",
        "endDate": datetime.now().strftime("%Y-%m-%d"),
        "dateFilterType": "BetweenStartDateAndEndDate"
    },
    "output": {
        "fields": [
            "event.startDate",
            "location.locality",
            "location.municipality.name",
            "taxon.vernacularName",
            "taxon.scientificName"
        ]
    },
    "paging": {
        "skip": 0,
        "take": 5000,
        "sortBy": "event.startDate",
        "sortOrder": "Asc"
    }
}

def skapa_checklista():
    print("📋 Skapar checklista från Artportalen (Högland, 2015–idag)...")

    try:
        response = requests.post(API_URL_BASE, headers=headers, json=payload, timeout=60)
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
        kommun = record.get("location", {}).get("municipality", {}).get("name", "okänd")

        if not art_lat:
            continue

        if art_lat not in arter:
            arter[art_lat] = {
                "art": art,
                "scientificName": art_lat,
                "första": datum,
                "sista": datum,
                "lokal": plats or "okänd plats",
                "kommuner": [kommun] if kommun else []
            }
        else:
            # Uppdatera sista sedd
            if datum and (not arter[art_lat]["sista"] or datum > arter[art_lat]["sista"]):
                arter[art_lat]["sista"] = datum
            # Samla kommuner
            if kommun and kommun not in arter[art_lat]["kommuner"]:
                arter[art_lat]["kommuner"].append(kommun)

    checklista = list(arter.values())
    checklista.sort(key=lambda x: (x["art"] or "").lower())

    Path("data").mkdir(parents=True, exist_ok=True)

    with open("data/checklista.json", "w", encoding="utf-8") as f:
        json.dump(checklista, f, ensure_ascii=False, indent=2)

    print(f"✅ Sparade {len(checklista)} unika arter till data/checklista.json")

if __name__ == "__main__":
    skapa_checklista()
