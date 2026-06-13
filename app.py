import streamlit as st
import bcrypt
import requests
import json
import os


# =========================================================
# engine/loader.py
# =========================================================
LOCAL_PATH = os.path.join(os.path.dirname(__file__), "data", "rumantsch.json")


def load_raw():
    # 1. Versuch: lokale Datei
    try:
        with open(LOCAL_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        pass

    # 2. Versuch: DATA_LINK
    try:
        data_link = st.secrets["DATA_LINK"]
        response = requests.get(data_link)
        response.raise_for_status()
        return json.loads(response.content.decode("utf-8-sig"))
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Fehler beim Laden der Daten: {e}")


# =========================================================
# engine/index_builder.py
# =========================================================
def build_index(raw):
    """
    Baut zwei Indizes aus den neuen JSON-Strukturen:
      - topics:  Liste von Grammatik-Themen (für Themen-Suche)
      - words:   Liste von Vokabel-Einträgen (für Voci-Suche)
    """
    topics = []
    words = []

    # --- Grammatik-Themen ---
    grammar = raw.get("grammar", {})
    for section in grammar.get("sections", []):
        section_title = section.get("title", "")

        # Sections mit "topics" (Lektionen)
        for topic in section.get("topics", []):
            topics.append({
                "section": section_title,
                "title": topic.get("title", ""),
                "data": topic,
            })

        # Sections mit "entries" direkt (z.B. Intro/Graphie)
        if "entries" in section and "topics" not in section:
            topics.append({
                "section": section_title,
                "title": section_title,
                "data": section,
            })

    # --- Vocabulari (Lectiuns) ---
    vocab = raw.get("vocabulary", {})
    for lect in vocab.get("lectiuns", []):
        lect_title = lect.get("title", "")
        for entry in lect.get("vocabulary", []):
            words.append({
                "source": lect_title,
                "voci": entry.get("vallader", ""),
                "translation": entry.get("deutsch", ""),
            })

    # --- Glossar ---
    glossar = raw.get("glossar", {})
    for entry in glossar.get("entries", []):
        if "vallader" not in entry:
            continue  # Buchstaben-Marker ("letter": "A") überspringen
        words.append({
            "source": "Glossar",
            "voci": entry.get("vallader", ""),
            "translation": entry.get("deutsch", ""),
        })

    return {"topics": topics, "words": words}


# =========================================================
# engine/search.py
# =========================================================
def search_words(index, query: str):
    q = query.lower().strip()
    results = []
    for w in index["words"]:
        if q in w["voci"].lower():
            results.append(w)
    return results


def search_topics(index, query: str):
    q = query.lower().strip().split()
    results = []
    for t in index["topics"]:
        text = f"{t['title']} {t['section']}".lower()
        if all(word in text for word in q):
            results.append(t)
    return results


# =========================================================
# engine/render.py
# =========================================================
def render_topic(t):
    section = t.get("section", "")
    title = t.get("title", "")
    data = t.get("data", {})

    st.subheader(f"🧩 {section}")
    st.markdown(f"**▶ {title}**")

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
            st.markdown(f"**{key}**")
            st.table([value["columns"]] + value["rows"])

    # Listen / Beispiele / entries / verbs / compounds etc.
    for key, value in data.items():
        if isinstance(value, list) and key not in ["rows"]:
            st.markdown(f"**{key}**")
            for v in value:
                if isinstance(v, dict):
                    if "examples" in v or "pattern" in v:
                        # Spezialfall: Aussprache-Einträge (intro)
                        pattern = v.get("pattern", "")
                        note = v.get("note", "")
                        examples = v.get("examples", [])
                        st.write(f"**{pattern}** – {note}")
                        if examples:
                            st.write(", ".join(str(e) for e in examples))
                    else:
                        st.write(" | ".join(str(x) for x in v.values()))
                else:
                    st.write(f"- {v}")

    # JSON RAW optional
    with st.expander("🧾 RAW DATA"):
        st.json(data)


def render_word(w):
    st.markdown(f"**{w['voci']}** — {w['translation']}")
    st.caption(f"Quelle: {w['source']}")


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

# Lade alle Daten (zuerst lokal, dann DATA_LINK)
raw = load_raw()
index = build_index(raw)

st.title("📘 Romanische Grammatik Explorer")

# Eingabe für Suche
query = st.text_input("Frage/Begriff eingeben:")

if query:
    word_results = search_words(index, query)
    topic_results = search_topics(index, query)

    if not word_results and not topic_results:
        st.warning("Keine Ergebnisse gefunden.")
    else:
        # Voci-Treffer: kompakt (Voci + Übersetzung)
        if word_results:
            st.markdown("### 📖 Vocabulari")
            for w in word_results:
                render_word(w)

        # Themen-Treffer: ausführlich (ganzes Thema)
        if topic_results:
            st.markdown("### 📚 Grammatik")
            for t in topic_results:
                render_topic(t)