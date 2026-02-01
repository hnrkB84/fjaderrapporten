"""
Körs en gång manuellt — hämtar alla kommuner och deras featureId
från Artportalen API. Sparar resultatet till data/kommuner.json.

Krav: OCP_APIM_SUBSCRIPTION_KEY satt som miljövariabel.
  Windows:  set OCP_APIM_SUBSCRIPTION_KEY=din_nyckel
  Sedan:    python3 hitta_kommuner.py
"""

import requests
import json
import os

API_KEY = os.getenv("OCP_APIM_SUBSCRIPTION_KEY")
AREAS_URL = "https://api.artdatabanken.se/species-observation-system/v1/Areas"

headers = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "X-Api-Version": "1.5"
}

# Vi söker kommuner i Jönköping-area men hämtar alla Municipality
# och filtrerar sedan på de vi behöver
HÖGLANDE_KOMMUNER = ["Eksjö", "Nässjö", "Aneby", "Tranås", "Vetlanda"]

def hitta_kommuner():
    print("🔍 Hämtar kommuner från Artportalen...")

    params = {
        "areaTypes": "Municipality"
    }

    try:
        res = requests.get(AREAS_URL, headers=headers, params=params, timeout=30)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Fel: {e}")
        return

    data = res.json()
    kommuner = data.get("records", [])

    print(f"\n📋 Totalt {len(kommuner)} kommuner hämtade.\n")
    print("=" * 50)
    print("HÖGLAND-KOMMUNER:")
    print("=" * 50)

    funna = {}
    for k in kommuner:
        namn = k.get("name", "")
        fid  = k.get("featureId", "")
        if namn in HÖGLANDE_KOMMUNER:
            funna[namn] = fid
            print(f"  {namn:15s} → featureId: {fid}")

    # Kontolla om alla hittades
    saknade = [n for n in HÖGLANDE_KOMMUNER if n not in funna]
    if saknade:
        print(f"\n⚠️  Hittade inte: {saknade}")
        print("   Sök manuellt i listan nedan:\n")
        for k in sorted(kommuner, key=lambda x: x.get("name", "")):
            print(f"    {k.get('name', ''):30s} featureId: {k.get('featureId', '')}")
    else:
        print("\n✅ Alla kommuner hittades!")

    # Spara till fil
    with open("data/kommuner.json", "w", encoding="utf-8") as f:
        json.dump(funna, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Sparade till data/kommuner.json")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ OCP_APIM_SUBSCRIPTION_KEY är inte satt.")
        print("   Windows: set OCP_APIM_SUBSCRIPTION_KEY=din_nyckel")
        print("   Sedan:   python3 hitta_kommuner.py")
    else:
        hitta_kommuner()
