import requests
import json
import time
from pathlib import Path

CHECKLISTA_FIL = Path("data/checklista.json")
UTFIL = Path("data/artljud.json")

XC_API = "https://xeno-canto.org/api/2.0/recordings"

def hamta_ljud_for_art(scientific_name):
    """Hämtar första tillgängliga ljud-URL från Xeno-Canto (högsta kvalitet)."""
    params = {
        "q": scientific_name,
        "page": 1,
        "per_page": 1,
        "sort": "quality",
        "order": "desc"
    }

    try:
        res = requests.get(XC_API, params=params, timeout=20)
        res.raise_for_status()
        data = res.json()

        results = data.get("results", [])
        if not results:
            print(f"⚠️ Hittade inget ljud för {scientific_name}")
            return {}

        rec = results[0]
        file_url = rec.get("file", "")

        if not file_url:
            print(f"⚠️ Ingen audio-URL i resultat för {scientific_name}")
            return {}

        return {
            "ljud": file_url,
            "ljud_lank": f"https://xeno-canto.org/recordings/{rec.get('key', '')}",
            "recordist": rec.get("recordist", ""),
            "land": rec.get("country", ""),
            "datum": rec.get("date", ""),
            "kvalitet": rec.get("quality", "")
        }

    except Exception as e:
        print(f"❌ Fel vid hämtning av ljud för {scientific_name}: {e}")
        return {}

def hamta_alla_ljud():
    print("🎵 Hämtar ljud från Xeno-Canto...")

    if not CHECKLISTA_FIL.exists():
        print("❌ Ingen checklista hittades — körs skapa_checklista.py först.")
        return

    with open(CHECKLISTA_FIL, encoding="utf-8") as f:
        checklista = json.load(f)

    # Läs befintlig cache
    if UTFIL.exists():
        with open(UTFIL, encoding="utf-8") as f:
            artljud = json.load(f)
    else:
        artljud = {}

    arter = sorted(set(
        art["scientificName"] for art in checklista
        if art.get("scientificName")
    ))
    print(f"🎶 {len(arter)} arter att söka ljud till.")

    nya = 0
    for artnamn in arter:
        if artnamn in artljud and artljud[artnamn].get("ljud"):
            print(f"⏭ Hoppar över (sparad): {artnamn}")
            continue

        print(f"🔄 Hämtar ljud för: {artnamn}...")
        artljud[artnamn] = hamta_ljud_for_art(artnamn)
        nya += 1
        time.sleep(2)  # Respekt för Xeno-Canto rate limits

        if nya % 15 == 0:
            print("⏳ Extra paus...")
            time.sleep(5)

    with open(UTFIL, "w", encoding="utf-8") as f:
        json.dump(artljud, f, ensure_ascii=False, indent=2)
    print(f"✅ Sparade ljud till {UTFIL}")

if __name__ == "__main__":
    hamta_alla_ljud()
