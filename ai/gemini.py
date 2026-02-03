import google.generativeai as genai
import json

genai.configure(api_key="AIzaSyCScg7BBvDw3ho9yDMJEHyD1vwewaggBTw")

model = genai.GenerativeModel("gemini-2.5-flash")

def get_ai_reply(message, tone="friendly"):
    msg_lower = message.lower()

    prompt = f"""
You are a {tone} AI chatbot.
Never say Google made you.

User: {message}
AI:
"""

    response = model.generate_content(prompt)
    return response.text