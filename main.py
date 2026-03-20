import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import OpenAI

# 1. API Setup
# I am using your NVIDIA key here. Make sure it is active!
API_KEY = os.getenv("NVIDIA_API_KEY", "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")

app = FastAPI(title="GymBot Backend")

# 2. Enable CORS (Crucial for Botpress)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to NVIDIA
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=API_KEY
)

# 3. Data Models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    system_prompt: str
    messages: List[Message]

@app.get("/")
def root():
    return {"status": "GymBot is Online 💪"}

# 4. The Main Chat Logic
@app.post("/chat")
def chat(req: ChatRequest):
    try:
        # STEP 1: Get info from Railway Variables OR use the 'Safety Net' below
        # This ensures the AI NEVER says "I don't have enough info"
        default_info = """
        Gym Name: IronForge Gym
        Agent Name: Sara
        Address: 123 Fitness Ave, Almaty
        Hours: Mon–Fri 6:00–23:00, Sat–Sun 8:00–22:00
        Phone: +7 777 123 4567
        Services: Personal Training (5,000 ₸), Group Classes, Sauna, Free Parking.
        Instructions: Always be warm and motivating. Offer a free trial day.
        """
        
        gym_knowledge = os.getenv("GYM_KNOWLEDGE", default_info)

        # STEP 2: Build the System Instruction
        system_instruction = f"""
        You are a professional Gym Manager. 
        USE THIS DATA ONLY:
        {gym_knowledge}
        
        RULES:
        - If the user's question isn't answered in the data, ask for their phone number.
        - Speak the same language as the user (English, Russian, or Kazakh).
        - Be friendly and encouraging.
        """

        # STEP 3: Format the conversation
        all_messages = [{"role": "system", "content": system_instruction}]
        for m in req.messages:
            all_messages.append({"role": m.role, "content": m.content})

        # STEP 4: Call NVIDIA Llama 3.1
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
