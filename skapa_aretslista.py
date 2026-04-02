"""
skapa_aretslista.py
-------------------
Kör en gång (eller vid behov) för att bygga den kompletta artlistan
för innevarande år från Artportalen.

Sparar data/aretslista.json — en post per unik art, sorterad på
senast sedd (nyaste först).

hamta_faglar.py håller sedan listan aktuell vid varje körning.
"""

import requests
import json
from datetime import datetime
from urllib.parse import quote_plus
from pathlib import Path
import os
import sys

API_KEY = os.getenv("OCP_APIM_SUBSCRIPTION_KEY")
API_URL_BASE = "https://api.artdatabanken.se/species-observation-system/v1/Observations/Search"

headers = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json",
    "X-Api-Version": "1.5"
}

AR = datetime.now().year

KOMMUNER = [
    {"areaType": "Municipality", "featureId": "686"},  # Eksjö
    {"areaType": "Municipality", "featureId": "684"},  # Nässjö
    {"areaType": "Municipality", "featureId": "682"},  # Aneby
    {"areaType": "Municipality", "featureId": "687"},  # Tranås
    {"areaType": "Municipality", "featureId": "688"},  # Vetlanda
]

def läs_json(path):
    if Path(path).exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

ARTBILDER_OVERRIDE = läs_json("data/artbilder_override.json")
ARTBILDER_AUTO     = läs_json("data/artbilder_auto.json")
ARTLJUD            = läs_json("data/artljud.json")

def hitta_override(namn):
    namn = namn.lower().strip()
    for key in ARTBILDER_OVERRIDE:
        if key.lower().strip() == namn:
            return ARTBILDER_OVERRIDE[key]
    return None

def bygg_aretslista():
    print(f"📋 Hämtar alla fågelfynd från {AR} (Högland)...")

    payload = {
        "skip": 0,
        "take": 1000,
        "sortBy": "event.startDate",
        "sortOrder": "Desc",
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
            "startDate": f"{AR}-01-01",
            "endDate":   f"{AR}-12-31",
            "dateFilterType": "BetweenStartDateAndEndDate"
        },
        "output": {
            "fields": [
                "event.startDate",
                "location.locality",
                "location.municipality.name",
                "taxon.vernacularName",
                "taxon.scientificName",
                "event.individualCount"
            ]
        }
    }

    # Paginera tills alla poster är hämtade
    records = []
    skip = 0
    take = 1000

    while True:
        payload["skip"] = skip
        payload["take"] = take
        try:
            resp = requests.post(API_URL_BASE, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Fel vid hämtning (skip={skip}): {e}")
            sys.exit(1)

        batch = resp.json().get("records", [])
        records.extend(batch)
        print(f"  → Hämtade {len(records)} poster totalt...")

        if len(batch) < take:
            break  # Inga fler poster
        skip += take

    print(f"✅ {len(records)} observationer hämtade totalt")

    # Deduplicera — en post per scientificName, behåll senaste datum
    artMap = {}
    for rec in records:
        art            = rec.get("taxon", {}).get("vernacularName", "okänd art")
        scientific     = rec.get("taxon", {}).get("scientificName", "").strip()
        datum_str      = rec.get("event", {}).get("startDate")
        locality       = rec.get("location", {}).get("locality", "")
        municipality   = rec.get("location", {}).get("municipality", {}).get("name", "okänd")
        plats          = locality or municipality

        if not scientific or not datum_str:
            continue

        # Bild
        override  = hitta_override(scientific)
        auto      = ARTBILDER_AUTO.get(scientific)
        bild      = (override or {}).get("bild")      or (auto or {}).get("bild")
        bild_lank = (override or {}).get("bild_lank") or (auto or {}).get("bild_lank")

        # Ljud
        ljud_data = ARTLJUD.get(scientific, {})
        ljud      = ljud_data.get("ljud")
        ljud_lank = ljud_data.get("ljud_lank")

        # Google Maps
        sokfras        = f"{plats}, {municipality}, Sverige"
        google_maps    = f"https://www.google.com/maps/search/?api=1&query={quote_plus(sokfras)}"

        if scientific not in artMap:
            artMap[scientific] = {
                "art":           art,
                "scientificName": scientific,
                "datum":         datum_str,
                "lokal":         plats,
                "kommun":        municipality,
                "bild":          bild,
                "bild_lank":     bild_lank,
                "ljud":          ljud,
                "ljud_lank":     ljud_lank,
                "googleMapsLank": google_maps
            }
        else:
            # Uppdatera om detta fynd är nyare
            if datum_str > artMap[scientific]["datum"]:
                artMap[scientific]["datum"]         = datum_str
                artMap[scientific]["lokal"]         = plats
                artMap[scientific]["kommun"]        = municipality
                artMap[scientific]["googleMapsLank"] = google_maps
            # Fyll på bild om den saknades
            if not artMap[scientific]["bild"] and bild:
                artMap[scientific]["bild"]      = bild
                artMap[scientific]["bild_lank"] = bild_lank

    # Sortera nyaste först
    lista = sorted(artMap.values(), key=lambda x: x["datum"], reverse=True)

    Path("data").mkdir(parents=True, exist_ok=True)
    with open("data/aretslista.json", "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

    print(f"💾 Sparade {len(lista)} unika arter till data/aretslista.json")

if __name__ == "__main__":
    bygg_aretslista()
