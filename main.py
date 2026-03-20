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
    gym_address: str
    training_price: str
    custom_prompt: str

# --- HELPER FUNCTIONS ---

def load_gym_info():
    """Loads settings from a file if it exists, otherwise uses defaults."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return f"""
            Gym Name: {data.get('gym_name')}
            Address: {data.get('gym_address')}
            Price: {data.get('training_price')}
            Instructions: {data.get('custom_prompt')}
            """
    return os.getenv("GYM_KNOWLEDGE", "Gym: IronForge, Price: 5000₸, Address: Almaty")

# --- ROUTES ---

@app.get("/status")
def get_status():
    return {"status": "GymBot is Online 💪"}

@app.get("/")
async def serve_home():
    return FileResponse("gym_chatbot.html")

@app.post("/save-settings")
async def save_settings(settings: SettingsUpdate):
    """Saves the gym details to a JSON file so the server remembers them."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.dict(), f)
    return {"message": "Settings saved successfully! Botpress is now updated."}

app.mount("/static", StaticFiles(directory="."), name="static")

# --- CHAT LOGIC (What Botpress Calls) ---

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        # Every time Botpress calls this, we load the LATEST saved info
        current_gym_knowledge = load_gym_info()

        system_instruction = f"""
        You are a professional Gym Manager. 
        USE THIS DATA ONLY:
        {current_gym_knowledge}
        
        RULES:
        - If the user's question isn't answered in the data, ask for their phone number.
        - Speak the same language as the user (English, Russian, or Kazakh).
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
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
