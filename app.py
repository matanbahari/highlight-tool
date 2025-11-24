
import streamlit as st
try:
    from PIL import Image
except Exception as e:
    raise ImportError("Pillow לא מותקן. הוסף 'pillow' ל-requirements.txt") from e

try:
    import pytesseract
except Exception as e:
    raise ImportError("pytesseract לא מותקן. הוסף 'pytesseract' ל-requirements.txt. שים לב: צריך גם את הבינארי של Tesseract במערכת.") from e

try:
    import requests
except Exception as e:
    raise ImportError("requests לא מותקן. הוסף 'requests' ל-requirements.txt") from e

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except Exception as e:
    raise ImportError("python-docx לא מותקן. הוסף 'python-docx' ל-requirements.txt") from e

try:
    import openai
except Exception as e:
    raise ImportError("openai לא מותקן. הוסף 'openai' ל-requirements.txt") from e

import io, re

# =========== הגדרות ===========
st.set_page_config(page_title="היילייטס סדרות", page_icon="📺", layout="wide")

# Secrets
try:
    TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
except Exception:
    TMDB_API_KEY = None

try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai.api_key = None

# ---------- פונקציות ----------
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\\n", " ").strip()
    text = re.sub(r"[^a-zA-Z0-9א-ת \\-]", "", text)
    return text

def extract_text_from_image(image: Image.Image) -> str:
    # אם המשתמש רוצה להשתמש ב-TESSERACT_CMD ספציפי ניתן להגדיר אותו ב-Secrets כ-TESSERACT_CMD
    tcmd = st.secrets.get("TESSERACT_CMD") if hasattr(st, "secrets") else None
    if tcmd:
        pytesseract.pytesseract.tesseract_cmd = tcmd
    try:
        raw = pytesseract.image_to_string(image, lang='heb+eng')
    except Exception as e:
        st.error("אירעה שגיאה בעת קריאה ל-pytesseract. ודא ש-Tesseract מותקן במערכת או הגדר TESSERACT_CMD ב-Secrets.")
        return ""
    return clean_text(raw)

def search_series_info(series_name: str) -> dict:
    if not TMDB_API_KEY:
        return {"name": series_name, "overview": "TMDB API key לא מוגדר ב-Secrets", "first_air_date": "לא ידוע", "episodes": "לא ידוע"}
    try:
        url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={series_name}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if not data.get("results"):
            return {"name": series_name, "overview": "לא נמצא מידע", "first_air_date": "לא ידוע", "episodes": "לא ידוע"}
        series = data["results"][0]
        return {
            "name": series.get("name", series_name),
            "overview": series.get("overview", "לא נמצא תקציר"),
            "first_air_date": series.get("first_air_date", "לא ידוע"),
            "episodes": series.get("number_of_episodes", "לא ידוע")
        }
    except Exception as e:
        return {"name": series_name, "overview": "שגיאה בשליפת המידע", "first_air_date": "לא ידוע", "episodes": "לא ידוע"}

def generate_summary(text: str) -> str:
    if not openai.api_key:
        return "OpenAI API key לא מוגדר ב-Secrets"
    if not text:
        return "אין טקסט לסיכום"
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "אתה מסכם טקסטים בעברית בקצרה ובבהירות."},
                {"role": "user", "content": f"צור תקציר קצר בעברית לטקסט הבא:\\n{text}"}
            ],
            max_tokens=200,
            temperature=0.2
        )
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return "שגיאה ביצירת תקציר עם OpenAI"

def create_highlights_doc(series_list: list) -> io.BytesIO:
    doc = Document()
    title = doc.add_paragraph("היילייטס סדרות", style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for s in series_list:
        doc.add_paragraph(s.get("name", ""), style="Heading 1")
        p_date = doc.add_paragraph(f"תאריך עלייה: {s.get('first_air_date','')}")
        p_date.runs[0].font.size = Pt(12)
        p_date.runs[0].font.color.rgb = RGBColor(0, 0, 128)
        doc.add_paragraph(f"מספר פרקים: {s.get('episodes','')}")
        doc.add_paragraph("תקציר:", style="Heading 2")
        doc.add_paragraph(s.get("summary",""))
        doc.add_paragraph("----------------------------------------")

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# =========== ממשק ===========
st.title("📺 כלי ליצירת היילייטס סדרות (מתוקן)")
st.write("העלה תמונות, ערוך את שם הסדרה שנחלץ במידת הצורך, וייצא Word.")

with st.sidebar:
    st.header("הגדרות")
    st.write("בדוק ש-Secrets כוללים: TMDB_API_KEY, OPENAI_API_KEY (אם רוצים תקצירים).")
    tess = st.text_input("Tesseract cmd (אם צריך)", value=st.secrets.get("TESSERACT_CMD","") if hasattr(st, "secrets") else "")
    if tess and "TESSERACT_CMD" not in st.secrets:
        st.info("כדי לשמור קבוע, הוסף את 'TESSERACT_CMD' ב-Secrets של האפליקציה במקום להקליד כאן.")

uploaded = st.file_uploader("בחר תמונות", type=["jpg","jpeg","png"], accept_multiple_files=True)
if not uploaded:
    st.info("העלה תמונה עם טקסט (צילום מסך של שם הסדרה או פוסטר עם טקסט).")
else:
    series_list = []
    for f in uploaded:
        st.markdown("---")
        cols = st.columns([1,2])
        with cols[0]:
            st.image(f, use_column_width=True, caption=f.name)
        with cols[1]:
            img = Image.open(f)
            with st.spinner("מפעיל OCR..."):
                extracted = extract_text_from_image(img)
            st.write("**טקסט שחולץ:**")
            st.write(extracted or "_לא זוהה טקסט_")

            # אפשרות לעריכה ידנית
            edited_name = st.text_input(f"ערוך שם סדרה (בעבור {f.name}):", value=extracted, key=f"name_{f.name}")
            if not edited_name:
                st.warning("לא הוזן שם -- לדלג על קובץ זה")
                continue

            # חפש ב-TMDB
            with st.spinner("מחפש TMDB..."):
                info = search_series_info(edited_name)

            # אפשר לערוך תקציר ידנית לפני שליחה ל-AI
            st.write("תקציר שנמצא ב-TMDB (ניתן לעריכה):")
            overview_edit = st.text_area(f"overview_{f.name}", value=info.get("overview",""), height=120)

            # כפתור לבקשת סיכום AI
            if st.button(f"ייצר תקציר AI עבור {f.name}", key=f"summarize_{f.name}"):
                with st.spinner("מייצר תקציר..."):
                    ai_summary = generate_summary(overview_edit)
                    st.success("התקציר נוצר")
                    st.write(ai_summary)
            else:
                ai_summary = overview_edit if overview_edit else "אין תקציר"

            st.write("----")
            st.write("סיכום סופי שיוכנס לקובץ:")
            st.write(ai_summary)

            info["summary"] = ai_summary
            info["name"] = edited_name
            series_list.append(info)

    if series_list:
        st.markdown("---")
        st.success("הכנת דוח להורדה")
        buf = create_highlights_doc(series_list)
        st.download_button("📥 הורד Word", data=buf, file_name="highlights.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
