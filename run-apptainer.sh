#!/bin/bash

HOST_IP=$(ip route get 1 | awk '{print $7; exit}')

export OLLAMA_HOST="http://${HOST_IP}:11434"
export JAEGER_HOST="http://${HOST_IP}:4317"
export MCP_HOST="http://${HOST_IP}:8000"

echo "Detected host IP: $HOST_IP"
echo "Using OLLAMA_HOST=$OLLAMA_HOST"
echo "Using JAEGER_HOST=$JAEGER_HOST"
echo "Using MCP_HOST=$MCP_HOST"

set -e

# Create directories for persistent volumes
mkdir -p ./volumes/ollama-data
mkdir -p ./apptainerdata/aitagent

# Cleanup function to stop all background processes
cleanup() {
  echo "Shutting down services..."
  kill $OLLAMA_PID $JAEGER_PID $AIT_MCP_PID 2>/dev/null
  wait $OLLAMA_PID $JAEGER_PID $AIT_MCP_PID 2>/dev/null || true
  echo "Cleanup complete"
}
trap cleanup EXIT

# Get absolute path to the directory (where this script is)
AITAGENT_DIR="$(cd "$(dirname "$0")"; pwd)"

echo "Starting Jaeger..."
apptainer exec \
  --net --network-args "portmap=16686:16686/tcp,portmap=4317:4317/tcp" \
  jaeger.sif \
  jaeger-all-in-one > /dev/null 2>&1 &

JAEGER_PID=$!

echo "Starting Ollama..."
# --nv exposes NVIDIA GPUs allocated by Slurm (via CUDA_VISIBLE_DEVICES)
apptainer exec \
  --bind "$(pwd)/volumes/ollama-data:/root/.ollama" \
  --env OLLAMA_MODELS=/root/.ollama/models \
  --env CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-all}" \
  --env OLLAMA_NUM_GPU=999 \
  --nv \
  ollama.sif \
  ollama serve > /dev/null 2>&1 &

OLLAMA_PID=$!

echo "Starting ait-mcp..."
apptainer exec \
  --env-file "$AITAGENT_DIR/.env" \
  ait-mcp.sif \
  python -m uvicorn main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &

AIT_MCP_PID=$!

sleep 5

echo "Starting aitagent..."
apptainer exec \
  --env OLLAMA_HOST=$OLLAMA_HOST \
  --env JAEGER_HOST=$JAEGER_HOST \
  --env MCP_HOST=$MCP_HOST \
  --env-file "$AITAGENT_DIR/.env" \
  --bind "$AITAGENT_DIR:/aitagent" \
  --pwd /aitagent \
  aitagent.sif \
  python run.py