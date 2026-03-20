import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import OpenAI

# 1. Configuration & API Setup
API_KEY = os.getenv("NVIDIA_API_KEY", "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")
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=API_KEY)

app = FastAPI(title="GymBot Live Scraper")

# Enable CORS for Botpress
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. The "Aggressive" Scraper Function
def get_live_site_data():
    url = "https://gymbot-production-a405.up.railway.app/"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Helper to find by ID (checks value, placeholder, then text)
        def find_by_id(element_id, backup_tag=None):
            el = soup.find(id=element_id)
            if el:
                return el.get('value') or el.get('placeholder') or el.text.strip()
            # If ID fails, try a generic tag like <h1> or <h2>
            if backup_tag:
                tag = soup.find(backup_tag)
                return tag.text.strip() if tag else None
            return None

        data = {
            "gym_name": find_by_id("gymName", "h1") or "Our Gym",
            "bot_name": find_by_id("botName") or "Sara",
            "location": find_by_id("gymLocation") or "Almaty",
            "prices": find_by_id("services") or "Please ask for current rates",
            "hours": find_by_id("gymHours") or "Standard Hours"
        }
        print(f"DEBUG: Scraped from site -> {data}")
        return data
    except Exception as e:
        print(f"Scraping error: {e}")
        return {
            "gym_name": "Our Gym",
            "bot_name": "Sara",
            "location": "Almaty",
            "prices": "12,000 ₸",
            "hours": "Mon-Fri 08:00-22:00"
        }

# 3. Data Structures
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    system_prompt: str = "ignored"
    messages: List[Message]

@app.get("/")
def root():
    return {"status": "GymBot Backend is active and scraping live site data! 💪"}

# 4. The Main Chat Logic
@
