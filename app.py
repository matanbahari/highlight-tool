import streamlit as st
from PIL import Image
import requests
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import openai
import base64
import re

OCR_KEY = st.secrets.get("OCR_API_KEY")
TMDB_KEY = st.secrets.get("TMDB_API_KEY")
openai.api_key = st.secrets.get("OPENAI_API_KEY")

st.set_page_config(page_title="היילייטס סדרות", page_icon="📺", layout="wide")

def extract_text_from_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    payload = {
        "base64Image": "data:image/png;base64," + img_base64,
        "language": "eng,heb",
        "apikey": OCR_KEY,
        "isOverlayRequired": False
    }
    try:
        r = requests.post("https://api.ocr.space/parse/image", data=payload)
        result = r.json()
        return result["ParsedResults"][0]["ParsedText"].strip()
    except:
        return ""

def clean_text(t):
    t = t.replace("\n", " ").strip()
    return re.sub(r"[^a-zA-Z0-9א-ת ]", "", t)

def search_series_info(series_name):
    if not TMDB_KEY:
        return {"name": series_name, "overview": "TMDB API key חסר", "first_air_date": "לא ידוע", "episodes": "לא ידוע"}
    try:
        url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_KEY}&query={series_name}"
        r = requests.get(url)
        data = r.json()
        if not data.get("results"):
            return {"name": series_name, "overview": "לא נמצא מידע", "first_air_date": "לא ידוע", "episodes": "לא ידוע"}
        s = data["results"][0]
        return {
            "name": s.get("name", series_name),
            "overview": s.get("overview", "אין תקציר"),
            "first_air_date": s.get("first_air_date", "לא ידוע"),
            "episodes": s.get("number_of_episodes", "לא ידוע")
        }
    except:
        return {"name": series_name, "overview": "שגיאת API", "first_air_date": "לא ידוע", "episodes": "לא ידוע"}

def generate_summary(text):
    if not openai.api_key:
        return "חסר מפתח OpenAI"
    try:
        r = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "סכם טקסטים בעברית."},
                {"role": "user", "content": f"צור תקציר בעברית:\n{text}"}
            ]
        )
        return r["choices"][0]["message"]["content"]
    except:
        return "שגיאה ביצירת תקציר"

def create_doc(series_list):
    doc = Document()
    title = doc.add_paragraph("היילייטס סדרות", style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for s in series_list:
        doc.add_paragraph(s["name"], style="Heading 1")
        p = doc.add_paragraph(f"תאריך עלייה: {s['first_air_date']}")
        p.runs[0].font.color.rgb = RGBColor(0,0,128)
        doc.add_paragraph(f"מספר פרקים: {s['episodes']}")
        doc.add_paragraph("תקציר:", style="Heading 2")
        doc.add_paragraph(s["summary"])
        doc.add_paragraph("----------------------------------------")
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

st.title("📺 היילייטס סדרות – ללא Tesseract")
uploaded = st.file_uploader("העלה תמונות", type=["jpg","jpeg","png"], accept_multiple_files=True)

if uploaded:
    series_list = []
    for img in uploaded:
        st.markdown("---")
        col1, col2 = st.columns([1,2])
        with col1:
            st.image(img, caption=img.name, use_column_width=True)
        with col2:
            with st.spinner("📤 מבצע OCR..."):
                text = extract_text_from_image(Image.open(img))
            cleaned = clean_text(text)
            st.write("טקסט שחולץ:", cleaned)
            if not cleaned:
                st.warning("לא נמצא טקסט.")
                continue
            with st.spinner("🔍 מחפש מידע..."):
                info = search_series_info(cleaned)
            with st.spinner("🤖 מייצר תקציר..."):
                summary = generate_summary(info["overview"])
            info["summary"] = summary
            series_list.append(info)
            st.success(f"🎬 {info['name']}")
            st.write(summary)
    if series_list:
        doc = create_doc(series_list)
        st.download_button(
            "📥 הורד Word",
            data=doc,
            file_name="highlights.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
