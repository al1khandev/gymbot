import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

app = FastAPI()

# 1. ALLOW CONECTION FROM YOUR MAC
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. INITIALIZE AI (Get your key from Railway Environment Variables)
# If you haven't set an API Key yet, the bot will use "Demo Mode"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-key-here"))

@app.get("/")
async def status():
    return {"status": "Online", "mode": "GymBot AI Production"}

@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        system_prompt = data.get("system_prompt", "You are a helpful gym assistant.")
        messages = data.get("messages", [])

        # Add the system instructions to the start of the AI's memory
        ai_payload = [{"role": "system", "content": system_prompt}] + messages

        # 3. ASK THE AI FOR A RESPONSE
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Or gpt-4o for better Kazakh/Russian
            messages=ai_payload,
            temperature=0.7
        )
        
        reply = response.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        # If no API key is found, it falls back to this message
        return {"reply": f"Connect your OpenAI Key in Railway to enable AI. (Error: {str(e)})"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
