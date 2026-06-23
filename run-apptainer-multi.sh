#!/bin/bash
# Usage: ./run-apptainer-multi.sh <instance> <gpu_id>
#   instance 0: ports 11434, 8000, 4317, 16686 (default)
#   instance 1: ports 11435, 8001, 4318, 16687
#
# Example - run two instances on two A100s:
#   ./run-apptainer-multi.sh 0 0 &
#   ./run-apptainer-multi.sh 1 1 &

INSTANCE=${1:-0}
GPU_ID=${2:-$INSTANCE}

# Port offsets per instance
OLLAMA_PORT=$((11434 + INSTANCE))
MCP_PORT=$((8000 + INSTANCE))
JAEGER_GRPC_PORT=$((4317 + INSTANCE))
JAEGER_UI_PORT=$((16686 + INSTANCE))

HOST_IP=$(ip route get 1 | awk '{print $7; exit}')

export OLLAMA_HOST="http://${HOST_IP}:${OLLAMA_PORT}"
export JAEGER_HOST="http://${HOST_IP}:${JAEGER_GRPC_PORT}"
export MCP_HOST="http://${HOST_IP}:${MCP_PORT}/mcp"

echo "=== Instance $INSTANCE (GPU $GPU_ID) ==="
echo "Host IP: $HOST_IP"
echo "OLLAMA_HOST=$OLLAMA_HOST"
echo "JAEGER_HOST=$JAEGER_HOST"
echo "MCP_HOST=$MCP_HOST"
echo ""

set -e

# Create directories for this instance
mkdir -p ./volumes/ollama-data-${INSTANCE}

# Cleanup function
cleanup() {
  echo "[Instance $INSTANCE] Shutting down services..."
  kill $OLLAMA_PID $JAEGER_PID $AIT_MCP_PID 2>/dev/null
  wait $OLLAMA_PID $JAEGER_PID $AIT_MCP_PID 2>/dev/null || true
  echo "[Instance $INSTANCE] Cleanup complete"
}
trap cleanup EXIT

AITAGENT_DIR="$(cd "$(dirname "$0")"; pwd)"

echo "[Instance $INSTANCE] Starting Jaeger..."
apptainer exec \
  --net --network-args "portmap=${JAEGER_UI_PORT}:16686/tcp,portmap=${JAEGER_GRPC_PORT}:4317/tcp" \
  jaeger.sif \
  jaeger-all-in-one > /dev/null 2>&1 &

JAEGER_PID=$!

echo "[Instance $INSTANCE] Starting Ollama on GPU $GPU_ID..."
apptainer exec \
  --bind "$(pwd)/volumes/ollama-data-${INSTANCE}:/root/.ollama" \
  --env OLLAMA_MODELS=/root/.ollama/models \
  --env CUDA_VISIBLE_DEVICES="${GPU_ID}" \
  --env OLLAMA_NUM_GPU=999 \
  --env OLLAMA_HOST="0.0.0.0:${OLLAMA_PORT}" \
  --nv \
  ollama.sif \
  ollama serve > /dev/null 2>&1 &

OLLAMA_PID=$!

echo "[Instance $INSTANCE] Starting ait-mcp on port $MCP_PORT..."
apptainer exec \
  --env-file "$AITAGENT_DIR/.env" \
  --env MCP_PORT=${MCP_PORT} \
  --pwd /ait-mcp \
  ait-mcp.sif \
  python run.py > /dev/null 2>&1 &

AIT_MCP_PID=$!

sleep 5

echo "[Instance $INSTANCE] Starting aitagent..."
apptainer exec \
  --env OLLAMA_HOST=$OLLAMA_HOST \
  --env JAEGER_HOST=$JAEGER_HOST \
  --env MCP_HOST=$MCP_HOST \
  --env-file "$AITAGENT_DIR/.env" \
  --bind "$AITAGENT_DIR:/aitagent" \
  --pwd /aitagent \
  aitagent.sif \
  python run.py
