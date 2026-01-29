"""
KIO3 Service (Structuring: KIO3 -> KIO6)
Turning notes into formal requirements for the LLM
"""
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
import httpx

app = FastAPI(title="KIO3")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "kio3"}


async def _do_send_log(message: str):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post("http://kio_ui:8080/log", json={
                "service": "KIO3",
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
    Load message from messages.json and forward to KIO6.
    Simply passes through whatever JSON is defined in the file.
    """
    print(f"[KIO3] Received from KIO5: {request}", flush=True)
    await send_log(f"Received data from KIO5")
    
    # Load the message from messages.json
    try:
        with open('messages.json', 'r') as f:
            message = json.load(f)
        print(f"[KIO3] Loaded message: {message}", flush=True)
        await send_log(f"Structured data for patient {message.get('payload', {}).get('patient_id', 'unknown')}")
    except Exception as e:
        print(f"[KIO3] Error loading messages.json: {e}", flush=True)
        await send_log(f"Error loading messages.json: {str(e)}")
        # If no message file yet, just forward what we received
        message = request
    
    # Forward to KIO6
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"[KIO3] Forwarding to KIO6...", flush=True)
            await send_log("Forwarding to KIO6 (Validation)...")
            resp = await client.post("http://kio6:8002/process", json=message)
            print(f"[KIO3] Got response from KIO6", flush=True)
            await send_log("Received response from KIO6")
            return resp.json()
    except Exception as e:
        print(f"[KIO3] Error forwarding to KIO6: {e}", flush=True)
        await send_log(f"Error forwarding to KIO6: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to forward: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

