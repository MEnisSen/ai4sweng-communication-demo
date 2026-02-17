# Randomized Pipeline Demo

## Overview
The demo has been upgraded from a hardcoded 5-stage pipeline to a **dynamic randomized pipeline** that generates a different sequence each time you press "Start Pipeline".

## Key Changes

### 1. **Individual KIO Services (KIO2-KIO12)**
- Created separate directories for each KIO service: `kio2/`, `kio3/`, `kio4/`, etc.
- Each KIO has its own `app.py`, `Dockerfile`, `requirements.txt`, and `messages.json`
- All KIOs use the same dynamic routing logic but are independent containers
- Each KIO has an empty `messages.json` template with empty `header`, `payload`, and `metadata`

### 2. **Dynamic Pipeline Generation**
- When you click "Start Pipeline", the UI generates a random pipeline:
  - Randomly selects **3-8 KIOs** from the pool of KIO2-KIO12
  - Sorts them in ascending order for logical flow
  - Each run produces a different sequence
  
### 3. **Pipeline Routing**
- The pipeline configuration is embedded in the message:
  ```json
  {
    "pipeline": {
      "full_chain": ["KIO2", "KIO5", "KIO7", ...],
      "current_index": 0,
      "total_stages": 5
    },
    "header": {},
    "payload": {},
    "metadata": {}
  }
  ```
- Each KIO:
  1. Receives the message with pipeline config
  2. Loads its local `messages.json` (with empty payload/metadata)
  3. Updates the header with routing info
  4. Forwards to the next KIO in the chain
  5. The last KIO returns to the UI

### 4. **Updated UI**
- Shows the dynamically generated pipeline visually
- Button text: "🎲 Generate & Start Random Pipeline"
- Displays the actual pipeline that was executed after completion
- Color-coded service tags for KIO2-KIO12

## Example Pipelines Generated

### Test Run 1:
```
KIO2 → KIO3 → KIO5 → KIO6 → KIO9 → KIO10 → KIO11 → KIO12
(8 stages)
```

### Test Run 2:
```
KIO2 → KIO3 → KIO5 → KIO6 → KIO7 → KIO9 → KIO10 → KIO11
(8 stages)
```

### Test Run 3:
```
KIO2 → KIO4 → KIO8 → KIO10 → KIO11 → KIO12
(6 stages)
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                         UI Service                       │
│  - Generates random pipeline (3-8 KIOs from KIO2-KIO12) │
│  - Triggers first KIO with pipeline config              │
│  - Displays live logs and final result                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │   Random Pipeline (varies each run)   │
        │                                        │
        │   Example: KIO2 → KIO5 → KIO7 → KIO11 │
        └──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Generic KIO Services (KIO2-KIO12)          │
│  - Each KIO reads pipeline config from message          │
│  - Loads local messages.json (empty payload/metadata)   │
│  - Routes to next KIO in chain                          │
│  - Last KIO returns to UI                               │
└─────────────────────────────────────────────────────────┘
```

## How to Use

1. **Start the demo:**
   ```bash
   docker-compose up -d
   ```

2. **Access the UI:**
   Open http://localhost:8080 in your browser

3. **Generate and run a pipeline:**
   - Click "🎲 Generate & Start Random Pipeline"
   - Watch the live logs to see which KIOs are being executed
   - See the visual pipeline diagram
   - View the final result

4. **Run again for a different pipeline:**
   - Click the button again
   - A completely different sequence will be generated and executed

## Files Structure

```
ai4sweng_comm_demo/
├── docker-compose.yml          # Updated with KIO2-KIO12 services
├── ui/
│   ├── app.py                  # Updated with random pipeline logic
│   ├── Dockerfile
│   └── requirements.txt
├── kio2/                       # Individual KIO service
│   ├── app.py
│   ├── messages.json           # Empty template
│   ├── Dockerfile
│   └── requirements.txt
├── kio3/                       # Individual KIO service
│   ├── app.py
│   ├── messages.json
│   ├── Dockerfile
│   └── requirements.txt
├── kio4/ ... kio12/           # Same structure for all KIOs
└── RANDOMIZED_PIPELINE.md     # This documentation
```

## Testing

The system has been tested with multiple runs showing:
- ✅ Different pipelines generated each time
- ✅ Varying lengths (3-8 stages)
- ✅ All KIOs from the pool can be selected
- ✅ Messages flow correctly through the chain
- ✅ Empty payload/metadata preserved as requested
- ✅ Live logging works correctly
- ✅ UI displays the generated pipeline

## Next Steps (Optional)

- Add KIO-specific descriptions/roles to each service
- Implement actual processing logic in each KIO
- Add validation for pipeline constraints
- Store pipeline execution history
- Add metrics and monitoring

