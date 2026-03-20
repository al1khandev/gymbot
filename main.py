import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from openai import OpenAI

# 1. API Setup
API_KEY = os.getenv("NVIDIA_API_KEY", "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")
SETTINGS_FILE = "gym_settings.json"

app = FastAPI(title="GymBot Backend")

# 2. Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=API_KEY)

# 3. Data Models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    system_prompt: str
    messages: List[Message]

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

# --- HELPER FUNCTIONS ---

def load_gym_info():
    """Reads the JSON file to give the AI the latest gym data."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            return f"""
            Gym Name: {d.get('gym_name')}
            Address: {d.get('location')}
            Hours: {d.get('hours')}
            Phone: {d.get('phone')}
            PRICES: 1m: {d.get('price1m')}, 3m: {d.get('price3m')}, 6m: {d.get('price6m')}, 1y: {d.get('price1y')}, Drop-in: {d.get('priceDrop')}
            SERVICES: {d.get('services')}
            BOT PERSONA: Name is {d.get('bot_name')}. {d.get('custom_instructions')}
            """
    return "Gym: IronForge, Location: Almaty, Price: 12000₸"

# --- ROUTES ---

@app.get("/")
async def serve_home():
    return FileResponse("gym_chatbot.html")

@app.post("/save-settings")
async def save_settings(settings: SettingsUpdate):
    """Saves everything from your fancy HTML form to a file."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.dict(), f)
    return {"status": "success", "message": "Settings saved for Website and Botpress!"}

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        # We use the SAVED info if it exists, otherwise use the prompt sent by the request
        # This makes Botpress and the Web Preview both work perfectly.
        current_knowledge = load_gym_info()
        
        system_instruction = req.system_prompt
        if "IronForge" in current_knowledge: # Simple check to see if we have custom data
             system_instruction += f"\n\nUSE THIS UPDATED GYM DATA:\n{current_knowledge}"

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

app.mount("/", StaticFiles(directory=".", html=True), name="static")
