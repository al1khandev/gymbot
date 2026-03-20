import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import OpenAI

# 1. Setup
API_KEY = os.getenv("NVIDIA_API_KEY", "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")
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=API_KEY)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_site_data():
    url = "https://gymbot-production-a405.up.railway.app/"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This function pulls the 'value' (what you typed) or the text
        def grab(id_name, default):
            element = soup.find(id=id_name)
            if not element: return default
            # Check for <input value="..."> first, then fall back to inner text
            return element.get('value') or element.text.strip() or default

        data = {
            "gym_name": grab("gymName", "IronForge Gym"),
            "bot_name": grab("botName", "Sara"),
            "location": grab("gymLocation", "Almaty"),
            "prices": grab("services", "12,000 ₸ per month"),
            "hours": grab("gymHours", "08:00 - 22:00")
        }
        print(f"DEBUG: Scraped Data -> {data}") # This shows in Railway Logs
        return data
    except Exception as e:
        print(f"DEBUG: Scraping failed: {e}")
        return None

class ChatRequest(BaseModel):
    messages: List[dict]

@app.post("/chat")
def chat(req: ChatRequest):
    site = get_site_data()
    
    # We build the prompt using the LIVE data from your URL
    system_prompt = f"""
    You are {site['bot_name']}, the manager of {site['gym_name']}.
    LOCATION: {site['location']}
    PRICES: {site['prices']}
    HOURS: {site['hours']}
    
    RULES:
    - Use ONLY the information provided above.
    - If the user asks for a price, tell them {site['prices']}.
    - Be professional, warm, and motivating.
    - Respond in the user's language (English, Russian, or Kazakh).
    """

    try:
        messages = [{"role": "system", "content": system_prompt}] + req.messages
        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=messages,
            temperature=0.5
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
