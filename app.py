import base64
import fitz
import json
import os
from pathlib import Path

import bcrypt
import streamlit as st
from cryptography.fernet import Fernet

st.set_page_config(layout="wide")


# =========================================================
# engine/loader.py
# =========================================================
LOCAL_PATH = os.path.join(os.path.dirname(__file__), "data", "rumantsch.json")

ENCRYPTED_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "rumantsch.json.enc"
)


def load_raw():
    # 1. Versuch: unverschlüsselte lokale Datei
    try:
        with open(LOCAL_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        pass

    # 2. Versuch: verschlüsselte Datei
    try:
        key = st.secrets["FERNET_KEY"]

        with open(ENCRYPTED_PATH, "rb") as f:
            encrypted = f.read()

        fernet = Fernet(key.encode())
        decrypted = fernet.decrypt(encrypted)

        return json.loads(decrypted.decode("utf-8-sig"))

    except Exception as e:
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
    patterns = []

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

        # Sections mit "entries" direkt (z.B. Intro/Graphie und Aussprache)
        if "entries" in section and "topics" not in section:
            topics.append({
                "section": section_title,
                "title": section_title,
                "data": section,
            })

            # Einzelne Aussprache-Muster separat indexieren
            for entry in section["entries"]:
                if "pattern" in entry:
                    patterns.append({
                        "section": section_title,
                        "pattern": entry.get("pattern", ""),
                        "note": entry.get("note", ""),
                        "examples": entry.get("examples", []),
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

    return {"topics": topics, "words": words, "patterns": patterns}


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


def search_patterns(index, query: str):
    q = query.lower().strip()
    results = []
    for p in index["patterns"]:
        # Aussprache-Pattern wie "ca – co – cu" oder "gli – glü und –gl am Wortende"
        # in einzelne Tokens zerlegen und auf Gleichheit/Teilstring prüfen
        raw_pattern = p["pattern"].lower()
        tokens = [tok.strip() for tok in raw_pattern.replace("–", "-").split("-")]
        tokens = [tok for sub in tokens for tok in sub.split()]

        if q in tokens or q in raw_pattern:
            results.append(p)
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


def render_pattern(p):
    st.markdown(f"**{p['pattern']}** — {p['note']}")
    if p["examples"]:
        st.write(", ".join(str(e) for e in p["examples"]))
    st.caption(f"Quelle: {p['section']}")


def render_home_screen():
    """Zeigt das Auswahlmenü mit Explorer und PDF"""
    st.title("📘 Romanische Grammatik Explorer")
    st.markdown("---")
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("### 🔍 Explorer")
        st.markdown("Durchsuche Grammatik, Vokabeln und Aussprache.")
        if st.button("Zum Explorer", key="explorer_btn", use_container_width=True):
            st.session_state.view_mode = "explorer"
            st.rerun()
    
    with col2:
        st.markdown("### 📄 PDF")
        st.markdown("Öffne die vollständige PDF-Referenz.")
        if st.button("Zum PDF", key="pdf_btn", use_container_width=True):
            st.session_state.view_mode = "pdf"
            st.rerun()


def render_explorer_mode():
    """Suche und Filterung ohne PDF-Panel"""
    col1, col2 = st.columns([3, 0.3], gap="small")
    
    with col1:
        st.title("📘 Romanische Grammatik Explorer")
    
    with col2:
        if st.button("← Zurück", key="explorer_back"):
            st.session_state.view_mode = "home"
            st.rerun()
    
    st.markdown("---")
    
    # Eingabe für Suche
    query = st.text_input("Frage/Begriff eingeben:")

    if query:
        word_results = search_words(index, query)
        topic_results = search_topics(index, query)
        pattern_results = search_patterns(index, query)

        if not word_results and not topic_results and not pattern_results:
            st.warning("Keine Ergebnisse gefunden.")
        else:
            # Aussprache-Treffer: kompakt (Pattern + Erklärung + Beispiele)
            if pattern_results:
                st.markdown("### 🔊 Aussprache")
                for p in pattern_results:
                    render_pattern(p)

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


def render_pdf_mode():
    """PDF-Vollbildansicht mit allen Seiten"""
    col1, col2 = st.columns([3, 0.3], gap="small")
    
    with col1:
        st.markdown("# 📄 PDF Vollbildansicht")
    
    with col2:
        if st.button("← Zurück", key="pdf_back"):
            st.session_state.view_mode = "home"
            st.rerun()
    
    st.markdown("---")
    
    pdf_path = find_pdf_path()

    if not pdf_path:
        st.info("Keine PDF-Datei im Ordner data gefunden.")
        return

    page_images = render_pdf_pages(pdf_path)
    if not page_images:
        st.warning("Die PDF konnte nicht in Bilder umgewandelt werden.")
        return

    st.markdown("Scroll nach unten, um alle Seiten des PDFs in voller Breite zu sehen.")

    for page_num, image in page_images:
        st.image(image, caption=f"Seite {page_num}", use_column_width=True)


# =========================================================
# app.py
# =========================================================
def find_pdf_path():
    data_dir = Path(__file__).resolve().parent / "data"
    pdf_files = sorted(data_dir.glob("*.pdf"))
    return pdf_files[0] if pdf_files else None


@st.cache_data(show_spinner=False)
def render_pdf_pages(pdf_path: Path):
    doc = fitz.open(str(pdf_path))
    images = []
    zoom = 2.0
    matrix = fitz.Matrix(zoom, zoom)

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        png_bytes = pix.tobytes(output="png")
        images.append((page_number + 1, png_bytes))
    return images


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

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "home"

# Zeige die entsprechende Ansicht basierend auf view_mode
if st.session_state.view_mode == "home":
    render_home_screen()
elif st.session_state.view_mode == "explorer":
    render_explorer_mode()
elif st.session_state.view_mode == "pdf":
    render_pdf_mode()