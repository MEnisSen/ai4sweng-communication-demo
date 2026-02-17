"""
UI Service - User Interface for KIO Pipeline Demo
Triggers the pipeline and displays results
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List, Dict
import httpx
import json
import random

app = FastAPI(title="KIO UI")

# Store messages for visualization
pipeline_messages: Dict[str, list] = {}

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
    """Interactive web UI with flow visualization"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>KIO Pipeline Demo - Dynamic Flow Visualization</title>
        <style>
            * {
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #667eea;
                padding-bottom: 15px;
                margin-top: 0;
                font-size: 32px;
            }
            .subtitle {
                color: #666;
                font-size: 16px;
                margin-bottom: 20px;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 40px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 18px;
                font-weight: bold;
                margin: 20px 0;
                transition: transform 0.2s, box-shadow 0.2s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }
            button:disabled {
                background: #cccccc;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            /* Flow Visualization Panel */
            .flow-panel {
                background: #f8f9fa;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 30px;
                margin: 20px 0;
                min-height: 250px;
                display: none;
            }
            .flow-panel.active {
                display: block;
            }
            .flow-header {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .flow-canvas {
                display: flex;
                align-items: center;
                justify-content: center;
                flex-wrap: wrap;
                gap: 15px;
                padding: 20px;
            }
            .kio-node {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                color: white;
                font-size: 14px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                transition: transform 0.3s, box-shadow 0.3s;
                cursor: pointer;
                position: relative;
            }
            .kio-node:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 15px rgba(0,0,0,0.3);
            }
            .kio-node.active {
                animation: pulse 1s infinite;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            .flow-arrow {
                font-size: 32px;
                color: #667eea;
                cursor: pointer;
                transition: transform 0.2s, color 0.2s;
                position: relative;
                padding: 0 5px;
            }
            .flow-arrow:hover {
                transform: scale(1.2);
                color: #764ba2;
            }
            .flow-arrow.has-message {
                color: #4CAF50;
                font-weight: bold;
            }
            
            /* Message Modal */
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
                animation: fadeIn 0.3s;
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            .modal.active {
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .modal-content {
                background: white;
                padding: 30px;
                border-radius: 12px;
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                animation: slideIn 0.3s;
            }
            @keyframes slideIn {
                from { transform: translateY(-50px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            .modal-header {
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 15px;
                color: #333;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            .modal-close {
                float: right;
                font-size: 28px;
                font-weight: bold;
                color: #999;
                cursor: pointer;
                line-height: 20px;
            }
            .modal-close:hover {
                color: #333;
            }
            .message-content {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                white-space: pre-wrap;
                word-wrap: break-word;
                max-height: 400px;
                overflow-y: auto;
            }
            
            /* KIO Colors */
            .kio-color-UI { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .kio-color-2 { background: linear-gradient(135deg, #f44336 0%, #e91e63 100%); }
            .kio-color-3 { background: linear-gradient(135deg, #e91e63 0%, #9c27b0 100%); }
            .kio-color-4 { background: linear-gradient(135deg, #9c27b0 0%, #673ab7 100%); }
            .kio-color-5 { background: linear-gradient(135deg, #673ab7 0%, #3f51b5 100%); }
            .kio-color-6 { background: linear-gradient(135deg, #3f51b5 0%, #2196f3 100%); }
            .kio-color-7 { background: linear-gradient(135deg, #2196f3 0%, #03a9f4 100%); }
            .kio-color-8 { background: linear-gradient(135deg, #00bcd4 0%, #009688 100%); }
            .kio-color-9 { background: linear-gradient(135deg, #009688 0%, #4caf50 100%); }
            .kio-color-10 { background: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%); }
            .kio-color-11 { background: linear-gradient(135deg, #cddc39 0%, #ffeb3b 100%); color: #333; }
            .kio-color-12 { background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%); }
            
            /* Log Tags */
            .tag-KIO2 { background: #f44336; color: white; }
            .tag-KIO3 { background: #e91e63; color: white; }
            .tag-KIO4 { background: #9c27b0; color: white; }
            .tag-KIO5 { background: #673ab7; color: white; }
            .tag-KIO6 { background: #3f51b5; color: white; }
            .tag-KIO7 { background: #2196f3; color: white; }
            .tag-KIO8 { background: #00bcd4; color: white; }
            .tag-KIO9 { background: #009688; color: white; }
            .tag-KIO10 { background: #4caf50; color: white; }
            .tag-KIO11 { background: #cddc39; color: #333; }
            .tag-KIO12 { background: #ff9800; color: white; }
            .tag-UI { background: #607d8b; color: white; }
            
            .loading {
                display: none;
                color: #666;
                font-style: italic;
                font-size: 16px;
                text-align: center;
                padding: 20px;
            }
            .loading.active {
                display: block;
            }
            
            /* Logs Container */
            .logs-container {
                margin-top: 20px;
            }
            .logs-header {
                background: #333;
                color: white;
                padding: 12px 15px;
                border-radius: 8px 8px 0 0;
                font-weight: bold;
                font-size: 14px;
            }
            #live-logs {
                padding: 15px;
                background: #2d2d2d;
                color: #00ff00;
                border-radius: 0 0 8px 8px;
                font-family: 'Courier New', monospace;
                height: 300px;
                overflow-y: auto;
                font-size: 13px;
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
                padding: 3px 8px;
                border-radius: 4px;
                margin-right: 10px;
                font-size: 12px;
            }
            
            
            .info-box {
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #2196f3;
            }
            
            .input-container {
                margin: 20px 0;
            }
            
            .input-label {
                display: block;
                font-weight: bold;
                color: #333;
                margin-bottom: 8px;
                font-size: 16px;
            }
            
            .user-input {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
                resize: vertical;
                transition: border-color 0.3s;
            }
            
            .user-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .user-input::placeholder {
                color: #999;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 KIO Pipeline Demo - Dynamic Flow Visualization</h1>
            
            <div class="input-container">
                <label for="userInput" class="input-label">📝 Your Message:</label>
                <textarea id="userInput" class="user-input" placeholder="Enter your message here (e.g., 'Process patient data for analysis')..." rows="3"></textarea>
            </div>
            
            <button id="startBtn">🎲 Generate & Start Pipeline</button>
            
            <div class="loading" id="loading">⏳ Processing through pipeline stages...</div>
            
            <!-- Flow Visualization Panel -->
            <div class="flow-panel" id="flowPanel">
                <div class="flow-header">
                    <span>📊 Pipeline Flow Visualization</span>
                </div>
                <div class="flow-canvas" id="flowCanvas">
                    <!-- Pipeline nodes will be added here dynamically -->
                </div>
            </div>
            
            <!-- Message Modal -->
            <div class="modal" id="messageModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <span class="modal-close" onclick="closeModal()">&times;</span>
                        <span id="modalTitle">Message Details</span>
                    </div>
                    <div class="message-content" id="messageContent">
                        <!-- Message content will be displayed here -->
                    </div>
                </div>
            </div>
            
            <div class="logs-container">
                <div class="logs-header">📊 Live Logs</div>
                <div id="live-logs"></div>
            </div>
        </div>

        <script>
            let currentPipeline = [];
            let pipelineMessages = {};
            let activeKioIndex = -1;
            
            document.addEventListener('DOMContentLoaded', function() {
                const startBtn = document.getElementById('startBtn');
                const liveLogs = document.getElementById('live-logs');
                const flowPanel = document.getElementById('flowPanel');
                const flowCanvas = document.getElementById('flowCanvas');
                
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
                    
                    // Display pipeline when UI broadcasts it
                    if (data.service === 'UI' && data.data && data.data.pipeline && data.data.pipeline.full_chain) {
                        displayPipeline(data.data.pipeline.full_chain);
                    }
                    
                    // Update flow visualization
                    if (data.service && data.service.startsWith('KIO')) {
                        updateFlowVisualization(data);
                    }
                };
                    
                    socket.onclose = function() {
                        console.log('WebSocket disconnected, retrying...');
                        setTimeout(connectWebSocket, 1000);
                    };
                }
                
                connectWebSocket();
                
                function updateFlowVisualization(data) {
                    // Highlight active KIO
                    if (data.message && data.message.includes('Processing')) {
                        const kioNum = data.service.replace('KIO', '');
                        const kioIndex = currentPipeline.indexOf(data.service);
                        if (kioIndex !== -1) {
                            // Remove previous active
                            document.querySelectorAll('.kio-node').forEach(node => {
                                node.classList.remove('active');
                            });
                            // Add active to current
                            const currentNode = document.querySelector(`[data-kio="${data.service}"]`);
                            if (currentNode) {
                                currentNode.classList.add('active');
                                activeKioIndex = kioIndex;
                            }
                        }
                    }
                    
                    // Store message data for arrows
                    if (data.data && data.service.startsWith('KIO')) {
                        const kioIndex = currentPipeline.indexOf(data.service);
                        if (kioIndex !== -1 && kioIndex < currentPipeline.length - 1) {
                            const arrowKey = `${data.service}-${currentPipeline[kioIndex + 1]}`;
                            pipelineMessages[arrowKey] = data.data;
                            
                            // Mark arrow as having message
                            const arrow = document.querySelector(`[data-arrow="${arrowKey}"]`);
                            if (arrow) {
                                arrow.classList.add('has-message');
                            }
                        }
                    }
                }
                
                function displayPipeline(pipeline) {
                    currentPipeline = pipeline;
                    pipelineMessages = {};
                    activeKioIndex = -1;
                    
                    flowCanvas.innerHTML = '';
                    flowPanel.classList.add('active');
                    
                    pipeline.forEach((kio, index) => {
                        // Handle UI or KIO nodes
                        const kioNum = kio === 'UI' ? 'UI' : kio.replace('KIO', '');
                        
                        // Create KIO node
                        const kioNode = document.createElement('div');
                        kioNode.className = `kio-node kio-color-${kioNum}`;
                        kioNode.setAttribute('data-kio', kio);
                        kioNode.textContent = kio;
                        kioNode.title = `${kio} - Click to see details`;
                        flowCanvas.appendChild(kioNode);
                        
                        // Add arrow if not last
                        if (index < pipeline.length - 1) {
                            const arrow = document.createElement('div');
                            arrow.className = 'flow-arrow';
                            arrow.textContent = '→';
                            const arrowKey = `${kio}-${pipeline[index + 1]}`;
                            arrow.setAttribute('data-arrow', arrowKey);
                            arrow.title = 'Click to see message';
                            arrow.onclick = function() {
                                showMessage(arrowKey);
                            };
                            flowCanvas.appendChild(arrow);
                        }
                    });
                }
                
                function addLogEntry(data) {
                    const entry = document.createElement('div');
                    const time = new Date().toLocaleTimeString();
                    const serviceClass = `tag-${data.service}`;
                    
                    const hasDetailedData = data.data && typeof data.data === 'object';
                    entry.className = hasDetailedData ? 'log-entry has-data' : 'log-entry';
                    
                    const logContent = document.createElement('div');
                    logContent.innerHTML = `
                        <span class="timestamp">[${time}]</span>
                        <span class="service-tag ${serviceClass}">${data.service}</span>
                        <span>${data.message}</span>
                    `;
                    entry.appendChild(logContent);
                    
                    if (hasDetailedData) {
                        const detailDiv = document.createElement('div');
                        detailDiv.className = 'log-detail';
                        detailDiv.innerHTML = `<pre>${JSON.stringify(data.data, null, 2)}</pre>`;
                        entry.appendChild(detailDiv);
                        
                        entry.addEventListener('click', function() {
                            entry.classList.toggle('expanded');
                            detailDiv.classList.toggle('visible');
                        });
                    }
                    
                    liveLogs.appendChild(entry);
                    liveLogs.scrollTop = liveLogs.scrollHeight;
                }

                startBtn.addEventListener('click', async function() {
                    const button = document.getElementById('startBtn');
                    const loading = document.getElementById('loading');
                    const userInput = document.getElementById('userInput');
                    const userMessage = userInput.value.trim();
                    
                    // Validate input
                    if (!userMessage) {
                        alert('Please enter a message before starting the pipeline!');
                        userInput.focus();
                        return;
                    }
                    
                    // Clear previous state
                    liveLogs.innerHTML = '';
                    flowPanel.classList.remove('active');
                    
                    button.disabled = true;
                    loading.classList.add('active');
                    
                    try {
                        const response = await fetch('/start', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ user_prompt: userMessage })
                        });
                        
                        if (!response.ok) {
                            throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                        }
                        
                        const data = await response.json();
                        console.log('Pipeline completed:', data);
                        
                    } catch (error) {
                        console.error('Error:', error);
                        alert('❌ Pipeline Error: ' + error.message);
                    } finally {
                        loading.classList.remove('active');
                        button.disabled = false;
                    }
                });
            });
            
            function showMessage(arrowKey) {
                const message = pipelineMessages[arrowKey];
                const modal = document.getElementById('messageModal');
                const modalTitle = document.getElementById('modalTitle');
                const messageContent = document.getElementById('messageContent');
                
                if (message) {
                    const [fromKio, toKio] = arrowKey.split('-');
                    modalTitle.textContent = `Message: ${fromKio} → ${toKio}`;
                    messageContent.textContent = JSON.stringify(message, null, 2);
                    modal.classList.add('active');
                } else {
                    modalTitle.textContent = 'No Message Data';
                    messageContent.textContent = 'No message data captured for this connection yet.';
                    modal.classList.add('active');
                }
            }
            
            function closeModal() {
                const modal = document.getElementById('messageModal');
                modal.classList.remove('active');
            }
            
            // Close modal when clicking outside
            window.onclick = function(event) {
                const modal = document.getElementById('messageModal');
                if (event.target === modal) {
                    modal.classList.remove('active');
                }
            }
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
async def start(request: dict = None):
    """
    Generate a random pipeline and execute it.
    UI is always the first KIO, followed by 2-7 random KIOs from KIO2-KIO12.
    """
    global pipeline_messages
    pipeline_messages = {}
    
    # Get user prompt from request
    if request is None:
        request = {}
    user_prompt = request.get("user_prompt", "")
    
    # Generate random pipeline: pick 2-7 KIOs from KIO2-KIO12
    all_kios = list(range(2, 13))  # [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    pipeline_length = random.randint(2, 7)
    selected_kios = random.sample(all_kios, pipeline_length)
    selected_kios.sort()  # Keep them in order for logical flow
    
    # UI is always first
    pipeline = ["UI"] + [f"KIO{k}" for k in selected_kios]
    
    print(f"\n{'='*60}", flush=True)
    print(f"[UI] 🎲 Generated random pipeline: {' → '.join(pipeline)}", flush=True)
    print(f"{'='*60}\n", flush=True)
    
    # Broadcast pipeline generation with pipeline data
    await manager.broadcast({
        "service": "UI",
        "message": f"🎲 Generated pipeline: {' → '.join(pipeline)}",
        "data": {
            "pipeline": {
                "full_chain": pipeline
            }
        }
    })
    
    # Create initial message with pipeline config and user prompt
    initial_message = {
        "pipeline": {
            "full_chain": pipeline,
            "current_index": 0,  # UI is at index 0
            "total_stages": len(pipeline)
        },
        "user_prompt": user_prompt,
        "header": {
            "source_kio": "UI"
        },
        "payload": {},
        "metadata": {}
    }
    
    # UI processes first, then forwards to first actual KIO
    # Skip UI (index 0) and start with first KIO (index 1)
    first_kio = pipeline[1].lower()  # e.g., "kio2"
    first_kio_num = selected_kios[0]
    port = 8000 + first_kio_num  # KIO2 = 8002, KIO3 = 8003, etc.
    
    # Update to reflect UI has processed and forwarding to first KIO
    initial_message["pipeline"]["current_index"] = 1
    initial_message["header"]["destination_kio"] = pipeline[1]
    
    # Broadcast that UI is processing
    await manager.broadcast({
        "service": "UI",
        "message": f"📥 Processing (stage 1/{len(pipeline)})",
        "data": {"user_prompt": user_prompt}
    })
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"[UI] → Forwarding to {pipeline[1]} at http://{first_kio}:{port}/process", flush=True)
            await manager.broadcast({
                "service": "UI",
                "message": f"📤 Forwarding to {pipeline[1]}...",
                "data": initial_message
            })
            
            response = await client.post(
                f"http://{first_kio}:{port}/process",
                json=initial_message
            )
            print(f"[UI] ← Received response status: {response.status_code}", flush=True)
            result = response.json()
            print(f"\n{'='*60}", flush=True)
            print(f"[UI] ✅ Pipeline completed successfully!", flush=True)
            print(f"{'='*60}\n", flush=True)
            
            await manager.broadcast({
                "service": "UI",
                "message": "✅ Pipeline completed successfully!",
                "data": {"pipeline": pipeline}
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
