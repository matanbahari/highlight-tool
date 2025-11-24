import subprocess
import sys

# --- פונקציה להתקנת חבילות ---
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# --- רשימת חבילות דרושות ---
required_packages = ["streamlit", "pillow", "requests", "python-docx", "openai"]

for pkg in required_packages:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        install(pkg)

# --- עכשיו כל החבילות זמינות ---
import streamlit as st
from PIL import Image
import requests
from docx import Document
from docx.shared import RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import base64
import re
import openai

# --- Secrets ---
OCR_KEY = st.secrets.get("OCR_API_KEY")
TMDB_KEY = st.secrets.get("TMDB_API_KEY")
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY")
if openai:
    openai.api_key = OPENAI_KEY

# --- פונקציות ---
def extract_text_from_image(image):
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
    if not TMDB_KEY:
        return {"name": name, "overview": """אין מפתח TMDB""", "first_air_date": """לא ידוע""", "episodes": """לא ידוע"""}
    try:
        url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_KEY}&query={name}"
        r = requests.get(url)
        data = r.json()
        if not data.get("results"):
            return {"name": name, "overview": """לא נמצא מידע""", "first_air_date": """לא ידוע""", "episodes": """לא ידוע"""}
        s = data["results"][0]
        return {"name": s.get("name", name), "overview": s.get("overview", """אין תקציר"""), "first_air_date": s.get("first_air_date", """לא ידוע"""), "episodes": s.get("number_of_episodes", """לא ידוע""")}
    except:
        return {"name": name, "overview": """שגיאת API""", "first_air_date": """לא ידוע""", "episodes": """לא ידוע"""}

def generate_summary(text):
    if not OPENAI_KEY:
        return """אין מפתח OpenAI"""
    try:
        r = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """סכם טקסטים בעברית"""},
                {"role": "user", "content": f"""סכם את הטקסט:\\n{text}"""}
            ],
            max_tokens=200
        )
        return r["choices"][0]["message"]["content"]
    except:
        return """שגיאה בסיכום"""

def create_doc(series_list):
    doc = Document()
    title = doc.add_paragraph("""היילייטס סדרות""", style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for s in series_list:
        doc.add_paragraph(s["name"], style="Heading 1")
        p = doc.add_paragraph(f"""תאריך עלייה: {s['first_air_date']}""")
        p.runs[0].font.color.rgb = RGBColor(0,0,128)
        doc.add_paragraph(f"""מספר פרקים: {s['episodes']}""")
        doc.add_paragraph("""תקציר:""", style="Heading 2")
        doc.add_paragraph(s["summary"])
        doc.add_paragraph("----------------------------------------")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# --- UI ---
st.set_page_config(page_title="Highlight Tool", page_icon="📺")
st.title("📺 כלי ליצירת היילייטס סדרות")

uploaded = st.file_uploader("""העלה תמונות""", type=["jpg","jpeg","png"], accept_multiple_files=True)

if uploaded:
    items = []
    for f in uploaded:
        st.markdown("---")
        image = Image.open(f)
        st.image(image, caption=f.name)
        with st.spinner("""מבצע OCR..."""):
            raw = extract_text_from_image(image)
        cleaned = clean_text(raw)
        st.write("טקסט שחולץ:", cleaned or """_לא נמצא טקסט_""")
        if cleaned:
            with st.spinner("""מחפש מידע..."""):
                info = search_series_info(cleaned)
            with st.spinner("""יוצר תקציר..."""):
                summary = generate_summary(info["overview"])
            info["summary"] = summary
            items.append(info)
            st.success(info["name"])
            st.write(summary)
    if items:
        buf = create_doc(items)
        st.download_button(
            """📥 הורד קובץ Word""",
            data=buf,
            file_name="highlights.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
