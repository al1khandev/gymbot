import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI

# ── Config ──────────────────────────────────────────────
API_KEY = os.getenv("NVIDIA_API_KEY", "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")
SETTINGS_FILE = "gym_settings.json"

DEFAULT_SETTINGS = {
    "gym_name": "IronForge Gym",
    "bot_name": "Sara",
    "location": "123 Fitness Ave, Almaty",
    "hours": "Mon–Fri 6:00–23:00, Sat–Sun 8:00–22:00",
    "phone": "+7 777 123 4567",
    "price1m": "12,000 ₸",
    "price3m": "30,000 ₸",
    "price6m": "54,000 ₸",
    "price1y": "96,000 ₸",
    "priceDrop": "2,500 ₸",
    "services": "Personal Training (from 5,000 ₸/session)\nGroup Classes (Yoga, HIIT, Boxing)\nNutrition Consultation\nSauna & Recovery Zone\nFree Parking\nLocker Rooms & Showers",
    "custom_instructions": "Always be warm and motivating. If someone seems hesitant about price, offer a free trial day. Respond in the same language the customer uses."
}

app = FastAPI(title="GymBot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=API_KEY)

# ── Models ───────────────────────────────────────────────
class SettingsUpdate(BaseModel):
    gym_name: Optional[str] = None
    location: Optional[str] = None
    hours: Optional[str] = None
    phone: Optional[str] = None
    price1m: Optional[str] = None
    price3m: Optional[str] = None
    price6m: Optional[str] = None
    price1y: Optional[str] = None
    priceDrop: Optional[str] = None
    services: Optional[str] = None
    bot_name: Optional[str] = None
    custom_instructions: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    system_prompt: Optional[str] = None
    messages: List[Message]

# ── Helpers ──────────────────────────────────────────────
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_SETTINGS

def save_settings_to_file(data: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ── Routes ───────────────────────────────────────────────
@app.get("/")
async def serve_home():
    if os.path.exists("gym_chatbot.html"):
        return FileResponse("gym_chatbot.html")
    return {"status": "GymBot backend is running 💪"}

@app.get("/get-settings")
async def get_settings():
    return load_settings()

@app.post("/save-settings")
async def save_settings(settings: SettingsUpdate):
    try:
        current = load_settings()
        updated = {**current, **{k: v for k, v in settings.dict().items() if v is not None}}
        save_settings_to_file(updated)
        return {"status": "success", "settings": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        gym = load_settings()

        system_instruction = req.system_prompt or f"""
You are {gym['bot_name']}, a friendly staff member at {gym['gym_name']}.
NEVER say you are an AI. You are a real person working at the gym.
Respond in the same language the customer uses.

GYM INFO:
- Name: {gym['gym_name']}
- Address: {gym['location']}
- Hours: {gym['hours']}
- Phone: {gym['phone']}

PRICES:
- 1 Month: {gym['price1m']}
- 3 Months: {gym['price3m']}
- 6 Months: {gym['price6m']}
- 1 Year: {gym['price1y']}
- Single Visit: {gym['priceDrop']}

SERVICES:
{gym['services']}

INSTRUCTIONS:
{gym['custom_instructions']}
"""

        all_messages = [{"role": "system", "content": system_instruction}]
        for m in req.messages:
            all_messages.append({"role": m.role, "content": m.content})

        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=all_messages,
            max_tokens=1000,
            temperature=0.7
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
