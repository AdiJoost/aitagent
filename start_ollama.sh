#!/bin/bash
#SBATCH -p students
#SBATCH --job-name=ollama
#SBATCH --cpus-per-task=16
#SBATCH --mem=110G
#SBATCH --gres=gpu:2
#SBATCH --time=03:00:00
#SBATCH --output=ollama.out

set -e

echo "Running on node: $(hostname)"

# ---- CONFIG ----
WORKDIR=$PWD
DATA_DIR="$WORKDIR/volumes/ollama-data"
SIF="$WORKDIR/ollama.sif"
MODEL_FILE="$WORKDIR/models.txt"
PORT=11434

mkdir -p "$DATA_DIR"

# ---- NETWORK SETUP ----
HOST_IP=$(hostname -I | awk '{print $1}')
export OLLAMA_HOST="0.0.0.0:$PORT"

echo "Node IP: $HOST_IP"
echo "Ollama will run on port: $PORT"

# ---- START OLLAMA SERVER ----
echo "Starting Ollama..."
apptainer exec \
  --nv \
  --bind "$DATA_DIR:/root/.ollama" \
  --env OLLAMA_HOST=$OLLAMA_HOST \
  "$SIF" \
  ollama serve > ollama.log 2>&1 &

OLLAMA_PID=$!

# ---- WAIT FOR SERVER ----
echo "Waiting for Ollama to start..."
sleep 10

# ---- FUNCTION: CHECK IF MODEL EXISTS ----
model_exists() {
  local model="$1"
  apptainer exec \
    --nv \
    --bind "$DATA_DIR:/root/.ollama" \
    --env OLLAMA_HOST=$OLLAMA_HOST \
    "$SIF" \
    ollama list | grep -q "^$model"
}

# ---- PULL MODELS ----
echo "Processing models from $MODEL_FILE"

while read -r model || [ -n "$model" ]; do
  # skip empty/comment lines
  [[ -z "$model" || "$model" =~ ^# ]] && continue

  echo "----------------------------------"
  echo "Model: $model"

  if model_exists "$model"; then
    echo "Already present → skipping"
  else
    echo "Pulling $model..."
    apptainer exec \
      --nv \
      --bind "$DATA_DIR:/root/.ollama" \
      --env OLLAMA_HOST=$OLLAMA_HOST \
      "$SIF" \
      ollama pull "$model"
  fi

done < "$MODEL_FILE"

echo "----------------------------------"
echo "All models ready."

# ---- PRINT TUNNEL INFO ----
echo ""
echo "To connect from your laptop:"
echo "ssh -L $PORT:$(hostname):$PORT $USER@nickel.fhgr.ch -t ssh nickel.fhgr.ch"
echo ""
echo "Then use:"
echo "export OLLAMA_HOST=http://localhost:$PORT"

# ---- KEEP JOB ALIVE ----
wait $OLLAMA_PID