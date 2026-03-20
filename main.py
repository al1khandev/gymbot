import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import OpenAI

# 1. API Setup
API_KEY = os.getenv("NVIDIA_API_KEY", "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")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=API_KEY
)

# Function to "Read" your website live
def get_live_site_data():
    url = "https://gymbot-production-a405.up.railway.app/"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # We find the info using the IDs from your HTML tags
        # Note: We look for 'value' because they are <input> tags
        data = {
            "name": soup.find(id="gymName")["value"] if soup.find(id="gymName") else "Our Gym",
            "location": soup.find(id="gymLocation")["value"] if soup.find(id="gymLocation") else "Almaty",
            "hours": soup.find(id="gymHours")["value"] if soup.find(id="gymHours") else "Standard Hours",
            "phone": soup.find(id="gymPhone")["value"] if soup.find(id="gymPhone") else "Contact us",
            "services": soup.find(id="services").text if soup.find(id="services") else "Fitness",
            "bot_name": soup.find(id="botName")["value"] if soup.find(id="botName") else "Assistant",
            "extra": soup.find(id="customInstructions").text if soup.find(id="customInstructions") else ""
        }
        return data
    except Exception as e:
        print(f"Scraping error: {e}")
        return None

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    system_prompt: str
    messages: List[Message]

@app.post("/chat")
def chat(req: ChatRequest):
    # 1. READ THE SITE LIVE
    site_info = get_live_site_data()
    
    # 2. CREATE THE PROMPT FROM SITE DATA
    if site_info:
        knowledge = f"""
        Gym Name: {site_info['name']}
        Agent Name: {site_info['bot_name']}
        Location: {site_info['location']}
        Hours: {site_info['hours']}
        Phone: {site_info['phone']}
        Services/Prices: {site_info['services']}
        Special Instructions: {site_info['extra']}
        """
    else:
        knowledge = "We are a professional gym in Almaty."

    system_instruction = f"""
    You are {site_info['bot_name'] if site_info else 'the manager'}. 
    Use ONLY this data: {knowledge}
    Rules:
    - Respond in the user's language (English, Russian, or Kazakh).
    - If info is missing, ask for a phone number.
    - Be motivating.
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
        raise HTTPException(status_code=500, detail=str(e))
