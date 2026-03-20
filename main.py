import os
import json
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

app = FastAPI(title="GymBot Full Backend")

# Enable CORS for your Website and Botpress
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This file will act as your "Memory" so changes stay saved
DATA_FILE = "data.json"

# Ensure the data file exists when the app starts
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({
            "gym_name": "Our Gym",
            "bot_name": "Sara",
            "location": "Almaty",
            "prices": "12,000 ₸",
            "hours": "08:00 - 22:00"
        }, f)

# 2. Data Models
class GymSettings(BaseModel):
    gym_name: str
    bot_name: str
    location: str
    prices: str
    hours: str

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

# 3. Routes for the Website to Save/Load
@app.get("/settings")
def get_settings():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

@app.post("/save-settings")
def save_settings(settings: GymSettings):
    with open(DATA_FILE, "w") as f:
        json.dump(settings.dict(), f)
    return {"status": "success", "message": "Settings saved to data.json"}

# 4. The Live Scraper (Backup)
def get_live_site_data():
    url = "https://gymbot-production-a405.up.railway.app/"
    try:
        # We try to get the LATEST info from the live URL
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        def find_by_id(element_id):
            el = soup.find(id=element_id)
            if el:
                return el.get('value') or el.text.strip()
            return None

        return {
            "gym_name": find_by_id("gymName"),
            "bot_name": find_by_id("botName"),
            "location": find_by_id("gymLocation"),
            "prices": find_by_id("services"),
            "hours": find_by_id("gymHours")
        }
    except:
        return None

# 5. The Main Chat Logic
@app.post("/chat")
def chat(req: ChatRequest):
    # 1. First, check your saved "Memory" (data.json)
    with open(DATA_FILE, "r") as f:
        site = json.load(f)
    
    # 2. Try to update with live site data if available
    live_data = get_live_site_data()
    if live_data:
        # Only overwrite if the live data actually found something
        for key in site:
            if live_data.get(key):
                site[key] = live_data[key]

    system_instruction = f"""
    You are {site['bot_name']}, the manager of {site['gym_name']}.
    Location: {site['location']}
    Prices: {site['prices']}
    Hours: {site['hours']}
    Speak the user's language (English, Russian, or Kazakh). Be motivating!
    """

    try:
        all_messages = [{"role": "system", "content": system_instruction}]
        for m in req.messages:
            all_messages.append({"role": m.role, "content": m.content})

        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=all_messages,
            max_tokens=500
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail="AI Service Down")

@app.get("/")
def health_check():
    return {"status": "Online", "storage": "data.json active"}
