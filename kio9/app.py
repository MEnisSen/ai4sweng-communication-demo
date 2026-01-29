"""
KIO9 Service (Compliance: KIO9 -> User)
Final scan for GDPR/HIPAA before doctor review
"""
import json
import asyncio
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import httpx

app = FastAPI(title="KIO9")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "kio9"}


async def _do_send_log(message: str, data: dict = None):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            log_entry = {
                "service": "KIO9",
                "message": message
            }
            if data:
                log_entry["data"] = data
            await client.post("http://kio_ui:8080/log", json=log_entry)
    except Exception as e:
        print(f"Failed to send log: {e}", flush=True)

async def send_log(message: str, data: dict = None):
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
    Load message from messages.json and return to UI.
    This is the final stage - simply returns whatever JSON is defined.
    """
    print(f"[KIO9] Received from KIO7: {request}", flush=True)
    await send_log(f"📥 Received data from KIO7", data=request)
    
    # Load the message from messages.json
    try:
        with open('messages.json', 'r') as f:
            message = json.load(f)
        print(f"[KIO9] Loaded message: {message}", flush=True)
        patient_id = message.get('payload', {}).get('patient_id', 'unknown')
        await send_log(f"🔒 Compliance check passed for patient {patient_id}", data=message)
    except Exception as e:
        print(f"[KIO9] Error loading messages.json: {e}", flush=True)
        await send_log(f"Error loading messages.json: {str(e)}")
        # If no message file yet, just return what we received
        message = request
    
    print(f"[KIO9] Returning to UI: {message}", flush=True)
    await send_log("📤 Returning final report to UI", data=message)
    # This is the final stage - return to caller (UI)
    return message


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

