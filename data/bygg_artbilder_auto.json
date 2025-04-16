import requests
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Fil med dina fågelobservationer (från hamta_faglar.py)
OBSERVATIONSFIL = "data/eksjo_faglar_apiresponse.json"
UTFIL = "data/artbilder_auto.json"

# Hämtar bilddata från Magnus Commons API baserat på vetenskapligt namn
def hamta_bild_info(artnamn):
    url = f"https://magnus-toolserver.toolforge.org/commonsapi.php?search={artnamn.replace(' ', '+')}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        rot = ET.fromstring(res.content)
        bildinfo = rot.find("file")
        if bildinfo is not None:
            return {
                "bild": bildinfo.findtext("url"),
                "bild_lank": bildinfo.findtext("descriptionurl")
            }
    except Exception as e:
        print(f"❌ Kunde inte hämta bild för {artnamn}: {e}")
    return {"bild": None, "bild_lank": None}

# Huvudfunktion som bygger artbilds-uppslag
def bygg_artbilder():
    print("🔍 Läser in observationer...")
    if not Path(OBSERVATIONSFIL).exists():
        print(f"❌ Filen {OBSERVATIONSFIL} saknas.")
        return

    with open(OBSERVATIONSFIL, encoding="utf-8") as f:
        data = json.load(f)

    unika_arter = {}
    for obs in data:
        nyckel = obs["scientificName"].strip()
        if nyckel and nyckel not in unika_arter:
            unika_arter[nyckel] = None

    print(f"🔎 Hittade {len(unika_arter)} unika arter att söka bilder till.")
    artbilder = {}

    for artnamn in unika_arter:
        print(f"🔄 Hämtar bild till: {artnamn}...")
        bilddata = hamta_bild_info(artnamn)
        artbilder[artnamn] = bilddata

    with open(UTFIL, "w", encoding="utf-8") as f:
        json.dump(artbilder, f, ensure_ascii=False, indent=2)
    print(f"✅ Sparade bilduppslag till {UTFIL}")

if __name__ == "__main__":
    bygg_artbilder()
