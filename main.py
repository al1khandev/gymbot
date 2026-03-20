import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import OpenAI

# 1. Configuration & API Setup
# I kept your key here as requested, but remember to keep this file private!
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
                # Try to get 'value' (for inputs) or 'text' (for <h1>/<span>)
                return el.get('value') or el.get('placeholder') or el.get_text().strip()
            
            # If ID fails, try a generic tag like <h1> as a backup
            if backup_tag:
                tag = soup.find(backup_tag)
                return tag.get_text().strip() if tag else None
            return None

        data = {
            "gym_name": find_by_id("gymName", "h1") or "Our Gym",
            "bot_name": find_by_id("botName") or "Sara",
            "location": find_by_id("gymLocation") or "Almaty",
            "prices": find_by_id("services") or "12,000 ₸ per month",
            "hours": find_by_id("gymHours") or "08:00 - 22:00"
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
@app.post("/chat")
def chat(req: ChatRequest):
    # Get the latest data from your website URL
    site = get_live_site_data()
    
    # Force the AI to use the scraped information
    system_instruction = f"""
    You are {site['bot_name']}, the manager of {site['gym_name']}.
    
    KNOWLEDGE BASE (FROM WEBSITE):
    - Gym Name: {site['gym_name']}
    - Location: {site['location']}
    - Prices & Services: {site['prices']}
    - Operating Hours: {site['hours']}
    
    RULES:
    - Use ONLY the information provided above.
    - If the user asks for a price, you must say: {site['prices']}.
    - Speak the same language as the user (English, Russian, or Kazakh).
    - Be professional, warm, and highly motivating.
    """

    try:
        # Prepare messages for the AI
        all_messages = [{"role": "system", "content": system_instruction}]
        for m in req.messages:
            all_messages.append({"role": m.role, "content": m.content})

        # Call the Llama 3.1 model via NVIDIA
        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=all_messages,
            max_tokens=800,
            temperature=0.6
        )
        
        return {"reply": response.choices[0].message.content}

    except Exception as e:
        print(f"Error calling API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
