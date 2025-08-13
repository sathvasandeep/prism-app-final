import google.generativeai as genai
import os

API_KEY = os.getenv("GEMINI_API_KEY") or "<PUT_YOUR_KEY_HERE>"
genai.configure(api_key=API_KEY)

try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content("Say hello!")
    print("Gemini response:", getattr(resp, 'text', str(resp)))
except Exception as e:
    print("Gemini error:", e)
