import requests
import json
import time
from pathlib import Path

OBSERVATIONFIL = Path("data/eksjo_faglar_apiresponse.json")
UTFIL = Path("data/artbilder_auto.json")

WM_API = "https://commons.wikimedia.org/w/api.php"

def hamta_bildinfo(artnamn):
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": artnamn,
        "gsrlimit": 1,
        "prop": "imageinfo",
        "iiprop": "url"
    }
    try:
        res = requests.get(WM_API, params=params, timeout=20)
        res.raise_for_status()
        data = res.json()

        pages = data.get("query", {}).get("pages", {})
        for sida in pages.values():
            bild_url = sida.get("imageinfo", [{}])[0].get("url")
            filnamn = sida.get("title")
            if bild_url and filnamn:
                fil_url = f"https://commons.wikimedia.org/wiki/{filnamn.replace(' ', '_')}"
                return {"bild": bild_url, "bild_lank": fil_url}
    except Exception as e:
        print(f"❌ Kunde inte hämta bild för {artnamn}: {e}")
    return {}

def bygg_artbilder():
    print("🔍 Läser in observationer...")
    if not OBSERVATIONFIL.exists():
        print("❌ Ingen observationfil hittades.")
        return

    with open(OBSERVATIONFIL, encoding="utf-8") as f:
        observationer = json.load(f)

    # Läs in befintliga bilder för cache
    if UTFIL.exists():
        with open(UTFIL, encoding="utf-8") as f:
            artbilder = json.load(f)
    else:
        artbilder = {}

    arter = sorted(set(obs["scientificName"] for obs in observationer if obs.get("scientificName")))
    print(f"🔎 Hittade {len(arter)} unika arter att söka bilder till.")

    for artnamn in arter:
        if artnamn in artbilder and artbilder[artnamn].get("bild"):
            print(f"⏩ Hoppar över (redan sparad): {artnamn}")
            continue

        print(f"🔄 Hämtar bild till: {artnamn}...")
        artbilder[artnamn] = hamta_bildinfo(artnamn)
        time.sleep(1.5)  # Paus för att undvika 429-fel

    with open(UTFIL, "w", encoding="utf-8") as f:
        json.dump(artbilder, f, ensure_ascii=False, indent=2)
    print(f"✅ Sparade bilduppslag till {UTFIL}")

if __name__ == "__main__":
    bygg_artbilder()
