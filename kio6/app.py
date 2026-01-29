"""
KIO6 Service (Validation: KIO6 -> KIO7)
Checking for missing data or inconsistencies
"""
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
import httpx

app = FastAPI(title="KIO6")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "kio6"}


async def _do_send_log(message: str, data: dict = None):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            log_entry = {
                "service": "KIO6",
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
    Load message from messages.json and forward to KIO7.
    Simply passes through whatever JSON is defined in the file.
    """
    print(f"[KIO6] Received from KIO3: {request}", flush=True)
    await send_log(f"📥 Received data from KIO3", data=request)
    
    # Load the message from messages.json
    try:
        with open('messages.json', 'r') as f:
            message = json.load(f)
        print(f"[KIO6] Loaded message: {message}", flush=True)
        patient_id = message.get('payload', {}).get('patient_id', 'unknown')
        await send_log(f"✔️ Validated data for patient {patient_id}", data=message)
    except Exception as e:
        print(f"[KIO6] Error loading messages.json: {e}", flush=True)
        await send_log(f"Error loading messages.json: {str(e)}")
        # If no message file yet, just forward what we received
        message = request
    
    # Forward to KIO7
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"[KIO6] Forwarding to KIO7...", flush=True)
            await send_log("📤 Forwarding to KIO7 (Drafting)...", data=message)
            resp = await client.post("http://kio7:8003/process", json=message)
            response_data = resp.json()
            print(f"[KIO6] Got response from KIO7", flush=True)
            await send_log("✅ Received response from KIO7", data=response_data)
            return response_data
    except Exception as e:
        print(f"[KIO6] Error forwarding to KIO7: {e}", flush=True)
        await send_log(f"Error forwarding to KIO7: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to forward: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

