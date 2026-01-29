"""
KIO7 Service (Drafting: KIO7 -> KIO9)
Generating the medical report text (LLM Engine)
"""
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
import httpx

app = FastAPI(title="KIO7")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "kio7"}


async def _do_send_log(message: str):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post("http://kio_ui:8080/log", json={
                "service": "KIO7",
                "message": message
            })
    except Exception as e:
        print(f"Failed to send log: {e}", flush=True)

async def send_log(message: str):
    asyncio.create_task(_do_send_log(message))

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        await send_log(f"Request: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            await send_log(f"Error: {str(e)}")
            raise e

app.add_middleware(LogMiddleware)

@app.post("/process")
async def process(request: dict):
    """
    Load message from messages.json and forward to KIO9.
    Simply passes through whatever JSON is defined in the file.
    """
    print(f"[KIO7] Received from KIO6: {request}", flush=True)
    await send_log(f"Received data from KIO6")
    
    # Load the message from messages.json
    try:
        with open('messages.json', 'r') as f:
            message = json.load(f)
        print(f"[KIO7] Loaded message: {message}", flush=True)
        await send_log(f"Generated draft for patient {message.get('payload', {}).get('patient_id', 'unknown')}")
    except Exception as e:
        print(f"[KIO7] Error loading messages.json: {e}", flush=True)
        await send_log(f"Error loading messages.json: {str(e)}")
        # If no message file yet, just forward what we received
        message = request
    
    # Forward to KIO9
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"[KIO7] Forwarding to KIO9...", flush=True)
            await send_log("Forwarding to KIO9 (Compliance)...")
            resp = await client.post("http://kio9:8004/process", json=message)
            print(f"[KIO7] Got response from KIO9", flush=True)
            await send_log("Received response from KIO9")
            return resp.json()
    except Exception as e:
        print(f"[KIO7] Error forwarding to KIO9: {e}", flush=True)
        await send_log(f"Error forwarding to KIO9: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to forward: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

