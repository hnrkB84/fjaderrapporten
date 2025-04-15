import requests
import json
from datetime import datetime

headers = {
    "Ocp-Apim-Subscription-Key": "din-api-nyckel-hämtas-från-secrets",
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
        ]
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
            "recordedBy",
            "event.quantity",
            "event.activity"
        ]
    }
}

def hamta_fagelfynd():
    print("⏳ Hämtar fågelfynd från Artportalen...")

    full_url = "https://api.artdatabanken.se/species-observation-system/v1/Observations/Search?skip=0&take=15&sortBy=event.startDate&sortOrder=Desc"

    response = requests.post(full_url, headers=headers, json=payload, timeout=15)
    data = response.json()
    observationer = []

    for record in data.get("records", []):
        obs = {
            "art": record.get("taxon", {}).get("vernacularName", "okänd"),
            "scientificName": record.get("taxon", {}).get("scientificName", "okänt"),
            "datum": record.get("event", {}).get("startDate", ""),
            "lokal": record.get("location", {}).get("name", "okänd plats"),
            "rapporteradAv": record.get("recordedBy", "okänd observatör"),
            "antal": record.get("event", {}).get("quantity", 1),
            "observationstyp": record.get("event", {}).get("activity", "okänd")
        }
        observationer.append(obs)

    with open("data/eksjo_faglar_apiresponse.json", "w", encoding="utf-8") as f:
        json.dump(observationer, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(observationer)} observationer sparade.")

if __name__ == "__main__":
    hamta_fagelfynd()
