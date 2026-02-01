import requests
import json
import time
from pathlib import Path

CHECKLISTA_FIL = Path("data/checklista.json")
UTFIL = Path("data/artbilder_auto.json")

WM_API = "https://commons.wikimedia.org/w/api.php"

def hamta_bildinfo(artnamn):
    # Steg 1: Sök efter en fil i Wikimedia Commons
    search_params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": artnamn,
        "srnamespace": 6,  # Namespace 6 = File:
        "srlimit": 1
    }

    try:
        search_res = requests.get(WM_API, params=search_params, timeout=20)
        search_res.raise_for_status()
        search_data = search_res.json()

        if "query" not in search_data or not search_data["query"]["search"]:
            print(f"⚠️ Hittade ingen bildfil för {artnamn}.")
            return {}

        filtitel = search_data["query"]["search"][0]["title"]

        # Steg 2: Hämta bildens URL
        info_params = {
            "action": "query",
            "format": "json",
            "titles": filtitel,
            "prop": "imageinfo",
            "iiprop": "url"
        }

        info_res = requests.get(WM_API, params=info_params, timeout=20)
        info_res.raise_for_status()
        info_data = info_res.json()

        pages = info_data.get("query", {}).get("pages", {})
        for sida in pages.values():
            bild_url = sida.get("imageinfo", [{}])[0].get("url")
            if bild_url:
                fil_url = f"https://commons.wikimedia.org/wiki/{filtitel.replace(' ', '_')}"
                return {"bild": bild_url, "bild_lank": fil_url}
            else:
                print(f"⚠️ Hittade inte bild-URL i {filtitel}.")
                return {}

    except Exception as e:
        print(f"❌ Kunde inte hämta bild för {artnamn}: {e}")
        return {}

def bygg_artbilder():
    print("📸 Hämtar bilder från Wikimedia Commons...")

    if not CHECKLISTA_FIL.exists():
        print("❌ Ingen checklista hittades — körs skapa_checklista.py första.")
        return

    with open(CHECKLISTA_FIL, encoding="utf-8") as f:
        checklista = json.load(f)

    # Läs befintlig cache
    if UTFIL.exists():
        with open(UTFIL, encoding="utf-8") as f:
            artbilder = json.load(f)
    else:
        artbilder = {}

    arter = sorted(set(
        art["scientificName"] for art in checklista
        if art.get("scientificName")
    ))
    print(f"🖼 {len(arter)} arter att söka bilder till.")

    nya = 0
    for artnamn in arter:
        if artnamn in artbilder and artbilder[artnamn].get("bild"):
            print(f"⏭ Hoppar över (sparad): {artnamn}")
            continue

        print(f"🔄 Hämtar bild till: {artnamn}...")
        artbilder[artnamn] = hamta_bildinfo(artnamn)
        nya += 1
        time.sleep(3)

        if nya % 10 == 0:
            print("⏳ Extra paus...")
            time.sleep(5)

    with open(UTFIL, "w", encoding="utf-8") as f:
        json.dump(artbilder, f, ensure_ascii=False, indent=2)
    print(f"✅ Sparade bilduppslag till {UTFIL}")

if __name__ == "__main__":
    bygg_artbilder()
