from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import OpenAI

API_KEY = "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"

app = FastAPI(title="GymBot API")

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

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    system_prompt: str
    messages: List[Message]

@app.get("/")
def root():
    return {"status": "GymBot backend is running 💪"}

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        all_messages = [{"role": "system", "content": req.system_prompt}]
        all_messages += [{"role": m.role, "content": m.content} for m in req.messages]

        response = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=all_messages,
            max_tokens=1000
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
