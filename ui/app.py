"""
UI Service - User Interface for KIO Pipeline Demo
Triggers the pipeline and displays results
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List
import httpx
import json

app = FastAPI(title="KIO UI")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def index():
    """Simple web UI"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>KIO Pipeline Demo</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }
            .stage {
                display: inline-block;
                padding: 8px 15px;
                margin: 5px;
                background: #e3f2fd;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 500;
            }
            button {
                background: #4CAF50;
                color: white;
                padding: 15px 40px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 18px;
                font-weight: bold;
                margin: 20px 0;
            }
            button:hover {
                background: #45a049;
            }
            button:disabled {
                background: #cccccc;
                cursor: not-allowed;
            }
            #result {
                margin-top: 20px;
                padding: 20px;
                background: #f9f9f9;
                border-left: 4px solid #4CAF50;
                white-space: pre-wrap;
                display: none;
                max-height: 600px;
                overflow-y: auto;
                font-family: monospace;
                font-size: 13px;
            }
            .logs-container {
                margin-top: 20px;
            }
            .logs-header {
                background: #333;
                color: white;
                padding: 10px 15px;
                border-radius: 4px 4px 0 0;
                font-weight: bold;
                font-size: 14px;
            }
            #live-logs {
                padding: 15px;
                background: #2d2d2d;
                color: #00ff00;
                border-radius: 0 0 4px 4px;
                font-family: monospace;
                height: 300px;
                overflow-y: auto;
                min-height: 60px;
            }
            #live-logs:empty::after {
                content: 'Waiting for logs...';
                color: #888;
                font-style: italic;
            }
            .log-entry {
                margin-bottom: 5px;
                border-bottom: 1px solid #444;
                padding: 8px;
                cursor: pointer;
                transition: background-color 0.2s;
                border-radius: 4px;
            }
            .log-entry:hover {
                background: #3d3d3d;
            }
            .log-entry.has-data {
                padding-left: 20px;
                position: relative;
            }
            .log-entry.has-data::before {
                content: '▶';
                position: absolute;
                left: 5px;
                transition: transform 0.2s;
            }
            .log-entry.has-data.expanded::before {
                transform: rotate(90deg);
            }
            .log-detail {
                display: none;
                margin-top: 10px;
                padding: 10px;
                background: #1a1a1a;
                border-left: 3px solid #4CAF50;
                border-radius: 4px;
                font-size: 11px;
                color: #aaa;
                overflow-x: auto;
            }
            .log-detail.visible {
                display: block;
            }
            .timestamp {
                color: #888;
                margin-right: 10px;
            }
            .service-tag {
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 3px;
                margin-right: 10px;
            }
            .tag-KIO5 { background: #e91e63; color: white; }
            .tag-KIO3 { background: #9c27b0; color: white; }
            .tag-KIO6 { background: #2196f3; color: white; }
            .tag-KIO7 { background: #ff9800; color: white; }
            .tag-KIO9 { background: #4caf50; color: white; }
            
            .loading {
                display: none;
                color: #666;
                font-style: italic;
                font-size: 16px;
            }
            .info {
                background: #fff3cd;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
                border-left: 4px solid #ffc107;
            }
            .flow-diagram {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 30px 0;
                padding: 20px;
                background: #f0f0f0;
                border-radius: 8px;
            }
            .kio-box {
                background: #fff;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                text-align: center;
                font-weight: bold;
                min-width: 80px;
            }
            .arrow {
                font-size: 24px;
                color: #4CAF50;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 KIO Medical Report Pipeline Demo</h1>
            <p><strong>Pipeline Flow:</strong></p>
            <div>
                <span class="stage">1. KIO5 → KIO3 (Ingestion)</span>
                <span class="stage">2. KIO3 → KIO6 (Structuring)</span>
                <span class="stage">3. KIO6 → KIO7 (Validation)</span>
                <span class="stage">4. KIO7 → KIO9 (Drafting)</span>
                <span class="stage">5. KIO9 → User (Compliance)</span>
            </div>
            
            <div class="flow-diagram">
                <div class="kio-box">KIO5<br><small>Ingestion</small></div>
                <div class="arrow">→</div>
                <div class="kio-box">KIO3<br><small>Structuring</small></div>
                <div class="arrow">→</div>
                <div class="kio-box">KIO6<br><small>Validation</small></div>
                <div class="arrow">→</div>
                <div class="kio-box">KIO7<br><small>Drafting</small></div>
                <div class="arrow">→</div>
                <div class="kio-box">KIO9<br><small>Compliance</small></div>
            </div>
            
            <div class="info">
                <strong>ℹ️ How it works:</strong> Click the button below to trigger the pipeline. 
                Each KIO service will load its message from <code>messages.json</code> and forward it to the next stage.
                <br><strong>💡 Tip:</strong> Watch the Live Logs below to see the process in real-time!
            </div>
            
            <button id="startBtn">▶️ Start Pipeline Process</button>
            
            <div class="loading" id="loading">⏳ Processing through all 5 KIO stages...</div>
            
            <div class="logs-container">
                <div class="logs-header">📊 Live Logs</div>
                <div id="live-logs"></div>
            </div>
            
            <div id="result"></div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function() {
                console.log('DOM fully loaded and parsed');
                const startBtn = document.getElementById('startBtn');
                const liveLogs = document.getElementById('live-logs');
                
                // WebSocket Connection
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                let socket;

                function connectWebSocket() {
                    socket = new WebSocket(wsUrl);
                    
                    socket.onopen = function() {
                        console.log('WebSocket connected');
                    };
                    
                    socket.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        addLogEntry(data);
                    };
                    
                    socket.onclose = function() {
                        console.log('WebSocket disconnected, retrying...');
                        setTimeout(connectWebSocket, 1000);
                    };
                }
                
                connectWebSocket();
                
                function addLogEntry(data) {
                    const entry = document.createElement('div');
                    const time = new Date().toLocaleTimeString();
                    const serviceClass = `tag-${data.service}`;
                    
                    // Check if there's detailed data to show
                    const hasDetailedData = data.data && typeof data.data === 'object';
                    entry.className = hasDetailedData ? 'log-entry has-data' : 'log-entry';
                    
                    const logContent = document.createElement('div');
                    logContent.innerHTML = `
                        <span class="timestamp">[${time}]</span>
                        <span class="service-tag ${serviceClass}">${data.service}</span>
                        <span>${data.message}</span>
                    `;
                    entry.appendChild(logContent);
                    
                    // Add detailed data section if available
                    if (hasDetailedData) {
                        const detailDiv = document.createElement('div');
                        detailDiv.className = 'log-detail';
                        detailDiv.innerHTML = `<pre>${JSON.stringify(data.data, null, 2)}</pre>`;
                        entry.appendChild(detailDiv);
                        
                        // Make it clickable
                        entry.addEventListener('click', function() {
                            entry.classList.toggle('expanded');
                            detailDiv.classList.toggle('visible');
                        });
                    }
                    
                    liveLogs.appendChild(entry);
                    liveLogs.scrollTop = liveLogs.scrollHeight;
                }

                if (!startBtn) {
                    console.error('Start button not found!');
                    return;
                }

                startBtn.addEventListener('click', async function() {
                    console.log('Start button clicked');
                    const button = document.getElementById('startBtn');
                    const loading = document.getElementById('loading');
                    const result = document.getElementById('result');
                    
                    // Clear previous logs
                    liveLogs.innerHTML = '';
                    
                    button.disabled = true;
                    loading.style.display = 'block';
                    result.style.display = 'none';
                    
                    try {
                        console.log('Sending request to /start');
                        const response = await fetch('/start', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'}
                        });
                        
                        console.log('Response status:', response.status);
                        
                        if (!response.ok) {
                            throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                        }
                        
                        const data = await response.json();
                        console.log('Response data:', data);
                        result.textContent = '✅ Pipeline Complete!\\n\\n' + JSON.stringify(data, null, 2);
                        result.style.display = 'block';
                    } catch (error) {
                        console.error('Error:', error);
                        result.textContent = '❌ Error: ' + error.message;
                        result.style.display = 'block';
                    } finally {
                        loading.style.display = 'none';
                        button.disabled = false;
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ui"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/log")
async def receive_log(log_data: dict):
    """Receive logs from KIO services and broadcast to UI"""
    print(f"[UI-LOG] {log_data}", flush=True)
    await manager.broadcast(log_data)
    return {"status": "ok"}

@app.post("/start")
async def start():
    """
    Trigger the KIO pipeline starting with KIO5.
    No input needed - each KIO loads its own message from messages.json
    """
    print(f"\n{'='*60}", flush=True)
    print(f"[UI] 🚀 Starting KIO Pipeline Process", flush=True)
    print(f"{'='*60}\n", flush=True)
    
    # Broadcast start log
    await manager.broadcast({
        "service": "UI",
        "message": "🚀 Starting KIO Pipeline Process..."
    })
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"[UI] → Sending trigger to KIO5 at http://kio5:8001/process", flush=True)
            await manager.broadcast({
                "service": "UI",
                "message": "Triggering KIO5 (Ingestion)..."
            })
            
            response = await client.post(
                "http://kio5:8001/process",
                json={"trigger": "start"}
            )
            print(f"[UI] ← Received response status: {response.status_code}", flush=True)
            result = response.json()
            print(f"\n{'='*60}", flush=True)
            print(f"[UI] ✅ Pipeline completed successfully!", flush=True)
            print(f"{'='*60}\n", flush=True)
            
            await manager.broadcast({
                "service": "UI",
                "message": "✅ Pipeline completed successfully!"
            })
            
            return result
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"\n{'='*60}", flush=True)
        print(f"[UI] ❌ Pipeline error: {e}", flush=True)
        print(f"[UI] Full traceback:\n{error_detail}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        await manager.broadcast({
            "service": "UI",
            "message": f"❌ Pipeline error: {str(e)}"
        })
        
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

