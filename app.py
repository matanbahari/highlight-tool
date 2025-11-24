import streamlit as st
from PIL import Image
import pytesseract
import requests
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import openai

# שימוש ב-Secrets
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
openai.api_key = st.secrets["OPENAI_API_KEY"]

def extract_text_from_image(image):
    return pytesseract.image_to_string(image, lang='heb+eng').strip()

def search_series_info(series_name):
    url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={series_name}"
    response = requests.get(url)
    data = response.json()
    if data['results']:
        series = data['results'][0]
        return {
            "name": series.get('name', series_name),
            "overview": series.get('overview', 'לא נמצא תקציר'),
            "first_air_date": series.get('first_air_date', 'לא ידוע'),
            "episodes": series.get('number_of_episodes', 'לא ידוע')
        }
    return {"name": series_name, "overview": "לא נמצא מידע", "first_air_date": "", "episodes": ""}

def generate_summary(text):
    prompt = f"צור תקציר קצר בעברית עבור הטקסט הבא"
{text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "אתה מסכם טקסטים בעברית."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

def create_highlights_doc(series_list):
    doc = Document()
    title = doc.add_paragraph("היילייטס סדרות", style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for series_info in series_list:
        doc.add_paragraph(series_info['name'], style="Heading 1")
        p_date = doc.add_paragraph(f"תאריך עלייה: {series_info['first_air_date']}")
        p_date.runs[0].font.size = Pt(12)
        p_date.runs[0].font.color.rgb = RGBColor(0, 0, 128)
        doc.add_paragraph(f"מספר פרקים: {series_info['episodes']}")
        doc.add_paragraph("תקציר:", style="Heading 2")
        doc.add_paragraph(series_info['summary'], style="Normal")
        doc.add_paragraph("----------------------------------------")

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

st.title("📺 כלי ליצירת היילייטס סדרות")
st.write("העלה תמונות עם פרטי הסדרות וקבל קובץ Word עם ההיילייטס")

uploaded_images = st.file_uploader("בחר תמונות", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_images:
    series_list = []
    for uploaded_image in uploaded_images:
        image = Image.open(uploaded_image)
        st.image(image, caption=f"תמונה: {uploaded_image.name}", use_column_width=True)
        extracted_text = extract_text_from_image(image)
        st.write(f"**טקסט שחולץ:** {extracted_text}")
        if extracted_text:
            series_info = search_series_info(extracted_text)
            summary = generate_summary(series_info['overview'])
            series_info['summary'] = summary
            series_list.append(series_info)

    if series_list:
        doc_buffer = create_highlights_doc(series_list)
        st.download_button(
            label="📥 הורד קובץ Word",
            data=doc_buffer,
            file_name="highlights.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
