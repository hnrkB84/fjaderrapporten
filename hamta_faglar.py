import requests
import json
from datetime import datetime
from urllib.parse import urlencode

API_KEY = "38fd64de3bcb43628a457153476e476b"
API_URL_BASE = "https://api.artdatabanken.se/species-observation-system/v1/Observations/Search"

headers = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json",
    "X-Api-Version": "1.5"
}

ARTBILDER = {
    "Vigg": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Aythya_fuligula_female2.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Aythya_fuligula_female2.jpg"
    },
    "Ormvråk": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Buzzard_buteo_buteo.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Buzzard_buteo_buteo.jpg"
    },
    "Gransångare": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Phylloscopus_collybita_1.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Phylloscopus_collybita_1.jpg"
    },
    "Svarthätta": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Sylvia_atricapilla_male.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Sylvia_atricapilla_male.jpg"
    },
    "Rödstjärt": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Phoenicurus_phoenicurus_male_2.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Phoenicurus_phoenicurus_male_2.jpg"
    },
    "Sångsvan": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Cygnus_cygnus_1_(Piotr_Kuczynski).jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Cygnus_cygnus_1_(Piotr_Kuczynski).jpg"
    },
    "Brun kärrhök": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Circus_aeruginosus_male_flight.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Circus_aeruginosus_male_flight.jpg"
    },
    "Lövsångare": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Phylloscopus_trochilus.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Phylloscopus_trochilus.jpg"
    },
    "Svartvit flugsnappare": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Ficedula_hypoleuca_male_1.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Ficedula_hypoleuca_male_1.jpg"
    },
    "Röd glada": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Milvus_milvus_-England-8a.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Milvus_milvus_-England-8a.jpg"
    },
    "Svart rödstjärt": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Phoenicurus_ochruros_male_1.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Phoenicurus_ochruros_male_1.jpg"
    },
    "Orre": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Tetrao_tetrix_male.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Tetrao_tetrix_male.jpg"
    },
    "Skogsduva": {
        "bild": "https://commons.wikimedia.org/wiki/Special:FilePath/Columba_oenas1.jpg?width=120",
        "länk": "https://commons.wikimedia.org/wiki/File:Columba_oenas1.jpg"
    }
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

            art_nyckel = art.capitalize()  # Gör första bokstaven versal
            bild = ARTBILDER.get(art_nyckel, {}).get("bild")
            bild_lank = ARTBILDER.get(art_nyckel, {}).get("länk")


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
