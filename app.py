import streamlit as st
import base64
import io
import re

# Try imports and continue even if missing (shows errors instead of crash)
missing = []

try:
    from PIL import Image
except:
    Image = None
    missing.append("Pillow")

try:
    import requests
except:
    requests = None
    missing.append("requests")

try:
    from docx import Document
    from docx.shared import RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except:
    Document = None
    RGBColor = None
    WD_ALIGN_PARAGRAPH = None
    missing.append("python-docx")

try:
    import openai
except:
    openai = None
    missing.append("openai")

# UI
st.set_page_config(page_title="Highlight Tool", page_icon="📺")
st.title("📺 אפליקציית היילייטס – Debug Safe Mode")

# Missing modules
if missing:
    st.error("מודולים חסרים ולכן האפליקציה לא יכולה לרוץ:")
    for m in missing:
        st.write(f"- {m}")
    st.write("שימו בקובץ requirements.txt:")
    st.code("""streamlit
pillow
requests
python-docx
openai""")
    st.stop()

# Secrets
OCR_KEY = st.secrets.get("OCR_API_KEY")
TMDB_KEY = st.secrets.get("TMDB_API_KEY")
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY")

if openai:
    openai.api_key = OPENAI_KEY

# --- Functions ---

def extract_text_from_image(image):
    """OCR via OCR.space API"""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    payload = {
        "base64Image": "data:image/png;base64," + img_b64,
        "language": "heb,eng",
        "apikey": OCR_KEY or "helloworld"
    }

    try:
        r = requests.post("https://api.ocr.space/parse/image", data=payload)
        data = r.json()
        return data.get("ParsedResults", [{}])[0].get("ParsedText", "").strip()
    except:
        return ""


def clean_text(t):
    return re.sub(r"[^a-zA-Z0-9א-ת ]", "", t.replace("\n", " ")).strip()


def search_series_info(name):
    """TMDB lookup"""
    if not TMDB_KEY:
        return {
            "name": name,
            "overview": "אין מפתח TMDB",
            "first_air_date": "לא ידוע",
            "episodes": "לא ידוע"
        }

    try:
        url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_KEY}&query={name}"
        r = requests.get(url)
        data = r.json()

        if not data.get("results"):
            return {
                "name": name,
                "overview": "לא נמצא מידע",
                "first_air_date": "לא יד
