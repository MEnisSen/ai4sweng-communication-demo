"""
KIO5 Service (Ingestion: KIO5 -> KIO3)
Raw data collection and initial PII check
"""
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
import httpx

app = FastAPI(title="KIO5")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "kio5"}


async def _do_send_log(message: str, data: dict = None):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            log_entry = {
                "service": "KIO5",
                "message": message
            }
            if data:
                log_entry["data"] = data
            await client.post("http://kio_ui:8080/log", json=log_entry)
    except Exception as e:
        print(f"Failed to send log: {e}", flush=True)

async def send_log(message: str, data: dict = None):
    # Fire and forget logging
    asyncio.create_task(_do_send_log(message, data))

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
    Load message from messages.json and forward to KIO3.
    Simply passes through whatever JSON is defined in the file.
    """
    print(f"[KIO5] Received request: {request}", flush=True)
    await send_log(f"Received trigger request")
    
    # Load the message from messages.json
    try:
        with open('messages.json', 'r') as f:
            message = json.load(f)
        print(f"[KIO5] Loaded message: {message}", flush=True)
        patient_id = message.get('payload', {}).get('patient_id', 'unknown')
        await send_log(f"📥 Loaded message for patient {patient_id}", data=message)
    except Exception as e:
        print(f"[KIO5] Error loading messages.json: {e}", flush=True)
        await send_log(f"Error loading messages.json: {str(e)}")
        message = {"error": "Failed to load messages.json", "details": str(e)}
    
    # Forward to KIO3
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"[KIO5] Forwarding to KIO3...", flush=True)
            await send_log("📤 Forwarding to KIO3 (Structuring)...", data=message)
            resp = await client.post("http://kio3:8001/process", json=message)
            response_data = resp.json()
            print(f"[KIO5] Got response from KIO3", flush=True)
            await send_log("✅ Received response from KIO3", data=response_data)
            return response_data
    except Exception as e:
        import traceback
        print(f"[KIO5] Error forwarding to KIO3: {e}", flush=True)
        print(f"[KIO5] Traceback:\n{traceback.format_exc()}", flush=True)
        await send_log(f"Error forwarding to KIO3: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to forward: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

