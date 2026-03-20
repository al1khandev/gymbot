import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

app = FastAPI()

# 1. ALLOW CONNECTION FROM YOUR MAC
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. THE ENGINE
# PASTE YOUR nvapi-... KEY INSIDE THE QUOTES BELOW:
NVIDIA_KEY = "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"

client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=NVIDIA_KEY
)

@app.get("/")
async def status():
    return {"status": "Online", "engine": "NVIDIA NIM Active"}

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        system_prompt = data.get("system_prompt", "You are a helpful gym assistant.")
        messages = data.get("messages", [])

        # Construct the payload
        ai_payload = [{"role": "system", "content": system_prompt}] + messages

        # 3. CALL THE NVIDIA MODEL
        response = client.chat.completions.create(
            model="nvidia/llama-3.1-405b-instruct",
            messages=ai_payload,
            temperature=0.2,
            top_p=0.7,
            max_tokens=1024,
        )
        
        reply = response.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        return {"reply": f"System Error: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
