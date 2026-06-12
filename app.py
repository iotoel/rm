import streamlit as st
import bcrypt
import requests
import hashlib
import json


# =========================================================
# engine/cgu_builder.py
# =========================================================
def make_id(*parts):
    return hashlib.md5("::".join(parts).encode("utf-8")).hexdigest()


def build_cgu(raw):
    units = []

    for section in raw.get("sections", []):
        section_title = section.get("title", "")
        section_id = section.get("id", "")

        for topic in section.get("topics", []):
            topic_title = topic.get("title", "")

            unit_id = make_id(section_id, topic_title)

            units.append({
                "id": unit_id,
                "section": section_title,
                "topic": topic_title,
                "data": topic
            })

    return {"units": units}


# =========================================================
# engine/cgu_search.py
# =========================================================
def search_cgu(cgu, query: str):
    q = query.lower().strip().split()

    results = []

    for unit in cgu.get("units", []):
        topic = unit.get("topic", "").lower()
        section = unit.get("section", "").lower()

        text = f"{topic} {section}"

        if all(word in text for word in q):
            results.append(unit)

    return results


# =========================================================
# engine/loader.py
# =========================================================
def load_raw():
    data_link = st.secrets["DATA_LINK"]

    try:
        response = requests.get(data_link)
        response.raise_for_status()

        return json.loads(response.content.decode("utf-8-sig"))
        return data

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Fehler beim Laden der Daten: {e}")


def load_cgu():
    return build_cgu(load_raw())


# =========================================================
# app.py
# =========================================================
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