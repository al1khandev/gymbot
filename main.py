import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI

# 1. API Setup
# Use Environment Variable for security on Railway
API_KEY = os.getenv("NVIDIA_API_KEY", "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")
SETTINGS_FILE = "gym_settings.json"

app = FastAPI(title="GymBot Backend")

# 2. Enable CORS (Crucial so your Website and Botpress can talk to the API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=API_KEY)

# 3. Data Models
class SettingsUpdate(BaseModel):
    gym_name: str
    location: str
    hours: str
    phone: str
    price1m: str
    price3m: str
    price6m: str
    price1y: str
    priceDrop: str
    services: str
    bot_name: str
    custom_instructions: str

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    system_prompt: Optional[str] = None
    messages: List[Message]

# --- HELPER FUNCTIONS ---

def load_settings_from_file():
    """Helper to read the saved JSON data."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# --- ROUTES ---

@app.get("/")
async def serve_home():
    """Serves your fancy HTML dashboard."""
    return FileResponse("gym_chatbot.html")

@app.post("/save-settings")
async def save_settings(settings: SettingsUpdate):
    """Receives data from your website and saves it to a file."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings.dict(), f, ensure_ascii=False, indent=4)
        return {"status": "success", "message": "Settings updated for Botpress and Website!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-settings")
async def get_settings():
    """Botpress calls this to get the latest Gym info."""
    data = load_settings_from_file()
    if data:
        return data
    # Fallback if no settings have been saved yet
    return {
        "gym_name": "IronForge Gym",
        "bot_name": "Sara",
        "location": "Default Location",
        "price1m": "12000 ₸",
        "services": "General Fitness",
        "custom_instructions": "Be helpful."
    }

@app.post("/chat")
def chat(req: ChatRequest):
    """Used by the 'Test Chat' window on your website."""
    try:
        saved_data = load_settings_from_file()
        
        # Build the 'Brain' of the bot based on saved settings
        if saved_data:
            system_instruction = f"""
            You are {saved_data['bot_name']}, an assistant for {saved_data['gym_name']}.
            Address: {saved_data['location']}
            Hours: {saved_data['hours']}
            Prices: 1m({saved_data['price1m']}), 3m({saved_data['price3m']}), 1y({saved_data['price1y']}), Drop-in({saved_data['priceDrop']})
            Services: {saved_data['services']}
            Persona: {saved_data['custom_instructions']}
            """
        else:
            system_instruction = req.system_prompt or "You are a helpful gym assistant."

        all_messages = [{"role": "system", "content": system_instruction}]
        for m in req.messages:
            all_messages.append({"role": m.role, "content": m.content})

        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=all_messages,
            temperature=0.7
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files so images/scripts in the same folder work
app.mount("/", StaticFiles(directory=".", html=True), name="static")
