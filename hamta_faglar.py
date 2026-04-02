import requests
import json
from datetime import datetime
from urllib.parse import urlencode, quote_plus
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

# --- Hjälpfunktioner ---
def läs_json(path, default=None):
    if Path(path).exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}

ARTBILDER_OVERRIDE = läs_json("data/artbilder_override.json")
ARTBILDER_AUTO    = läs_json("data/artbilder_auto.json")
ARTLJUD           = läs_json("data/artljud.json")

def hitta_override(namn):
    namn = namn.lower().strip()
    for key in ARTBILDER_OVERRIDE:
        if key.lower().strip() == namn:
            return ARTBILDER_OVERRIDE[key]
    return None

# --- Kommuner i Högland ---
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
        "startDate": "2024-01-01",
        "endDate": "2026-12-31",
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

# --- Uppdatera årets artlista med nya fynd ---
def uppdatera_aretslista(nya_obs):
    """
    Läser befintlig data/aretslista.json och lägger till nya arter
    eller uppdaterar 'datum' om ett nyare fynd av samma art dyker upp.
    Sparar tillbaka sorterat på datum (nyaste först).
    """
    ar = datetime.now().year
    lista_path = "data/aretslista.json"

    # Läs befintlig lista som dict: scientificName -> post
    befintlig = läs_json(lista_path, default=[])
    artMap = {post["scientificName"]: post for post in befintlig}

    nya_arter = 0
    uppdaterade = 0

    for obs in nya_obs:
        # Filtrera bara innevarande år
        try:
            obs_ar = datetime.fromisoformat(obs["datum"]).year
        except Exception:
            continue
        if obs_ar != ar:
            continue

        key = obs["scientificName"]

        if key not in artMap:
            # Ny art — lägg till
            artMap[key] = {
                "art":            obs["art"],
                "scientificName": key,
                "datum":          obs["datum"],
                "lokal":          obs["lokal"],
                "kommun":         obs["kommun"],
                "bild":           obs["bild"],
                "bild_lank":      obs["bild_lank"],
                "ljud":           obs.get("ljud"),
                "ljud_lank":      obs.get("ljud_lank"),
                "googleMapsLank": obs["googleMapsLank"]
            }
            nya_arter += 1
            print(f"🆕 Ny art i årets lista: {obs['art']}")
        else:
            # Finns redan — uppdatera om detta fynd är nyare
            if obs["datum"] > artMap[key]["datum"]:
                artMap[key]["datum"]          = obs["datum"]
                artMap[key]["lokal"]          = obs["lokal"]
                artMap[key]["kommun"]         = obs["kommun"]
                artMap[key]["googleMapsLank"] = obs["googleMapsLank"]
                uppdaterade += 1
            # Fyll på bild om den saknades
            if not artMap[key].get("bild") and obs.get("bild"):
                artMap[key]["bild"]      = obs["bild"]
                artMap[key]["bild_lank"] = obs["bild_lank"]

    # Sortera nyaste datum först
    sorterad = sorted(artMap.values(), key=lambda x: x["datum"], reverse=True)

    with open(lista_path, "w", encoding="utf-8") as f:
        json.dump(sorterad, f, ensure_ascii=False, indent=2)

    print(f"📋 Årets artlista: {nya_arter} nya arter, {uppdaterade} uppdaterade → {len(sorterad)} totalt")

# --- Hämta senaste fågelfynd ---
def hamta_fagelfynd():
    print("📡 Hämtar fågelfynd från Artportalen (Högland)...")

    query_params = {
        "skip": 0,
        "take": 100,
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
            art              = record.get("taxon", {}).get("vernacularName", "Okänd art")
            scientific_name  = record.get("taxon", {}).get("scientificName", "Okänt namn").strip()
            datum_str        = record.get("event", {}).get("startDate", None)
            locality         = record.get("location", {}).get("locality", "")
            municipality     = record.get("location", {}).get("municipality", {}).get("name", "okänd kommun")
            plats            = locality or municipality
            observator       = record.get("recordedBy", "okänd observatör")
            antal            = record.get("event", {}).get("individualCount", 1)
            aktivitet        = record.get("event", {}).get("activity", "okänd")

            # Bild: override > auto
            override  = hitta_override(scientific_name)
            auto      = ARTBILDER_AUTO.get(scientific_name)
            bild      = (override or {}).get("bild")      or (auto or {}).get("bild")
            bild_lank = (override or {}).get("bild_lank") or (auto or {}).get("bild_lank")

            # Ljud
            ljud_data = ARTLJUD.get(scientific_name, {})
            ljud      = ljud_data.get("ljud")
            ljud_lank = ljud_data.get("ljud_lank")

            # Google Maps
            sokfras        = f"{plats}, {municipality}, Sverige"
            google_maps_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(sokfras)}"

            if override:
                print(f"🔸 Override användes för {scientific_name}")

            if datum_str:
                try:
                    formatted_date = datetime.fromisoformat(datum_str).isoformat()
                except ValueError:
                    formatted_date = datum_str

                observationer.append({
                    "art":             art,
                    "scientificName":  scientific_name,
                    "datum":           formatted_date,
                    "lokal":           plats,
                    "kommun":          municipality,
                    "rapporteradAv":   observator,
                    "antal":           antal,
                    "observationstyp": aktivitet,
                    "bild":            bild,
                    "bild_lank":       bild_lank,
                    "ljud":            ljud,
                    "ljud_lank":       ljud_lank,
                    "googleMapsLank":  google_maps_url
                })

        if observationer:
            with open("data/fagelfynd.json", "w", encoding="utf-8") as f:
                json.dump(observationer, f, ensure_ascii=False, indent=2)
            print(f"💾 Sparade {len(observationer)} fynd till data/fagelfynd.json")

            # Uppdatera årets artlista med nya fynd
            uppdatera_aretslista(observationer)
        else:
            print("⚠️ Inga observationer sparade — listan är tom.")

    except Exception as e:
        print(f"❌ Fel vid hantering av data: {e}")

if __name__ == "__main__":
    hamta_fagelfynd()
