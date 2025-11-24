import streamlit as st
missing = []

# Defensive imports
try:
    from PIL import Image
except Exception:
    Image = None
    missing.append("Pillow (PIL)")

try:
    import requests
except Exception:
    requests = None
    missing.append("requests")

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except Exception:
    Document = None
    Pt = None
    RGBColor = None
    WD_ALIGN_PARAGRAPH = None
    missing.append("python-docx")

try:
    import openai
except Exception:
    openai = None
    missing.append("openai")

try:
    import base64, io, re
except Exception:
    base64 = None
    io = None
    re = None

# UI setup
st.set_page_config(page_title="Highlight Tool", page_icon="📺", layout="wide")
st.title("📺 אפליקציית היילייטס – Debug Mode")

# Missing modules display
if missing:
    st.error("יש מודולים חסרים:")
    for m in missing:
        st.write(f"- **{m}**")
    st.write("שים בקובץ requirements.txt:")
    st.code("""
streamlit
pillow
requests
python-docx
openai
    """)
    st.stop()

# Load secrets
OCR_KEY = st.secrets.get("OCR_API_KEY")
TMDB_KEY = st.secrets.get("TMDB_API_KEY")
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY")

openai.api_key = OPENAI_KEY

# OCR function
def extract_text_from_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    payload = {
        "base64Image": "data:image/png;base64," + img_base64,
        "language": "eng,heb",
        "apikey": OCR_KEY or "helloworld",
        "isOverlayRequired": False
    }

    try:
        r = requests.post("https://api.ocr.space/parse/image", data=payload)
        result = r.json()
        return result.get("ParsedResults", [{}])[0].get("ParsedText", "").strip()
    except Exception:
        return ""

# Clean text
def clean_text(t):
    return re.sub(r"[^a-zA-Z0-9א-ת ]", "", (t or "").replace("\n", " ").strip())

# TMDB search
def search_series_info(series_name):
    if not TMDB_KEY:
        return {
            "name": series_name,
            "overview": "TMDB key חסר",
            "first_air_date": "לא ידוע",
            "episodes": "לא ידוע"
        }

    try:
        url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_KEY}&query={series_name}"
        r = requests.get(url)
        data = r.json()

        if not data.get("results"):
            return {
                "name": series_name,
                "overview": "לא נמצא מידע",
                "first_air_date": "לא ידוע",
                "episodes": "לא ידוע"
            }

        s = data["results"][0]
        return {
            "name": s.get("name", series_name),
            "overview": s.get("overview", "אין תקציר"),
            "first_air_date": s.get("first_air_date", "לא ידוע"),
            "episodes": s.get("number
