import streamlit as st
import bcrypt

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Passwort", type="password")

    if st.button("Anmelden"):
        stored_hash = st.secrets["PASSWORD_HASH"]

        if bcrypt.checkpw(
            password.encode(),
            stored_hash.encode()
        ):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Falsches Passwort")

    st.stop()

from engine.loader import load_cgu
from engine.cgu_search import search_cgu
import json

# Lade alle Daten
cgu = load_cgu()

st.title("📘 Romanische Grammatik Explorer")

# Eingabe für Suche
query = st.text_input("Frage/Begriff eingeben:")

if query:
    results = search_cgu(cgu, query)
    
    if not results:
        st.warning("Keine Ergebnisse gefunden.")
    else:
        for r in results:
            section = r.get("section", "Unknown section")
            topic = r.get("topic", "")
            data = r.get("data", {})

            st.subheader(f"🧩 {section}")
            st.markdown(f"**▶ {topic}**")

            # Notes
            for key in ["notes", "note", "notes2"]:
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        for n in val:
                            st.info(n)
                    else:
                        st.info(val)

            # Tabellen
            for key, value in data.items():
                if isinstance(value, dict) and "columns" in value and "rows" in value:
                    st.table([value["columns"]] + value["rows"])

            # Listen / Beispiele / entries
            for key, value in data.items():
                if isinstance(value, list) and key not in ["rows"]:
                    st.markdown(f"**{key}**")
                    for v in value:
                        if isinstance(v, dict):
                            st.write(" | ".join(str(x) for x in v.values()))
                        else:
                            st.write(f"- {v}")

            # JSON RAW optional
            with st.expander("🧾 RAW DATA"):
                st.json(data)