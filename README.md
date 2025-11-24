# כלי ליצירת היילייטס סדרות (גרסה מתקדמת)

## התקנה
1. התקן את הספריות:
```
pip install streamlit pytesseract pillow python-docx requests openai
```

2. הכנס את מפתחות ה-API שלך בקובץ `app.py`:
- TMDB_API_KEY
- OPENAI_API_KEY

3. הרץ את האפליקציה:
```
streamlit run app.py
```

## שימוש
- העלה כמה תמונות עם שמות סדרות.
- הכלי יבצע OCR, יחפש מידע ב-TMDb, ייצור תקציר עם GPT, ויאפשר הורדת קובץ Word מעוצב.
