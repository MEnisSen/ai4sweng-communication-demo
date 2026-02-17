"""
KIO7 Service - Dynamically routes based on pipeline config
"""
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
import httpx

KIO_NAME = "KIO7"
KIO_PORT = 8007

app = FastAPI(title=KIO_NAME)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": KIO_NAME}


async def _do_send_log(message: str, data: dict = None):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            log_entry = {
                "service": KIO_NAME,
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
    Process message and forward to next KIO in the pipeline.
    Pipeline config is embedded in the message.
    """
    print(f"[{KIO_NAME}] Received message", flush=True)
    
    pipeline_config = request.get("pipeline", {})
    full_chain = pipeline_config.get("full_chain", [])
    current_index = pipeline_config.get("current_index", 0)
    user_prompt = request.get("user_prompt", "")
    
    await send_log(f"📥 Processing (stage {current_index + 1}/{len(full_chain)})")
    
    # Load this KIO's specific message template (with empty payload/metadata)
    try:
        with open('messages.json', 'r') as f:
            kio_message = json.load(f)
        print(f"[{KIO_NAME}] Loaded message template", flush=True)
    except Exception as e:
        print(f"[{KIO_NAME}] No messages.json, using empty template", flush=True)
        kio_message = {
            "header": {},
            "payload": {},
            "metadata": {}
        }
    
    # Preserve user prompt in all messages
    kio_message["user_prompt"] = user_prompt
    
    # Update header with routing info
    next_index = current_index + 1
    kio_message["header"]["source_kio"] = KIO_NAME
    
    if next_index < len(full_chain):
        next_kio = full_chain[next_index]
        kio_message["header"]["destination_kio"] = next_kio
        
        # Update pipeline progress
        kio_message["pipeline"] = {
            "full_chain": full_chain,
            "current_index": next_index,
            "total_stages": len(full_chain)
        }
        
        # Forward to next KIO
        next_kio_lower = next_kio.lower()
        next_kio_num = int(next_kio.replace("KIO", ""))
        next_port = 8000 + next_kio_num
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"[{KIO_NAME}] Forwarding to {next_kio}...", flush=True)
                await send_log(f"📤 Forwarding to {next_kio}...", data=kio_message)
                
                resp = await client.post(
                    f"http://{next_kio_lower}:{next_port}/process",
                    json=kio_message
                )
                response_data = resp.json()
                
                print(f"[{KIO_NAME}] Got response from {next_kio}", flush=True)
                await send_log(f"✅ Received response from {next_kio}")
                return response_data
        except Exception as e:
            print(f"[{KIO_NAME}] Error forwarding to {next_kio}: {e}", flush=True)
            await send_log(f"Error forwarding to {next_kio}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to forward: {str(e)}")
    else:
        # This is the last KIO in the pipeline
        print(f"[{KIO_NAME}] Final stage - returning to UI", flush=True)
        await send_log("📤 Pipeline complete, returning to UI", data=kio_message)
        return kio_message


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=KIO_PORT)

