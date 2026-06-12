import json
import requests  # Für das Herunterladen der Daten von OneDrive
from pathlib import Path
from engine.cgu_builder import build_cgu

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data"
RAW_FILE = DATA_PATH / "grammar_raw.json"

def load_raw():
    # OneDrive-Link aus den Streamlit-Secrets abrufen
    import streamlit as st
    data_link = st.secrets["DATA_LINK"]

    try:
        # JSON-Datei von OneDrive herunterladen
        response = requests.get(data_link)
        response.raise_for_status()  # Fehler auslösen, falls der Download fehlschlägt

        # JSON-Daten laden
        data = response.json()

        #if "sections" not in data:
         #   raise ValueError("RAW JSON missing 'sections'")

        return data

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Fehler beim Laden der Daten: {e}")

def load_cgu():
    return build_cgu(load_raw())