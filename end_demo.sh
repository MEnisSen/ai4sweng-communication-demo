#!/bin/bash

echo "🛑 Stopping any running Docker containers..."
docker compose down

echo "🔍 Checking for port 8080 conflicts..."
PID=$(lsof -t -i:8080)

if [ ! -z "$PID" ]; then
    echo "⚠️  Found process $PID using port 8080. Killing it..."
    kill -9 $PID
    echo "✅ Process killed."
else
    echo "✅ Port 8080 is free."
fi