#!/bin/bash

set -e

# Create directories for persistent volumes
mkdir -p ./volumes/ollama-data
mkdir -p ./apptainerdata/aitagent

# Convert docker images to SIF files (if not already done)
echo "Pulling and converting Docker images to SIF..."

# Disable cache explicitly for each build
echo "Building Ollama image..."
SINGULARITY_DISABLE_CACHE=True apptainer build --force ollama.sif docker://ollama/ollama

echo "Building aitagent image..."
SINGULARITY_DISABLE_CACHE=True apptainer build --force aitagent.sif docker://adijida/aitagent:latest

echo "Building ait-mcp image..."
SINGULARITY_DISABLE_CACHE=True apptainer build --force ait-mcp.sif docker://adijida/ait-mcp:latest

echo "Building Jaeger image..."
SINGULARITY_DISABLE_CACHE=True apptainer build --force jaeger.sif docker://jaegertracing/jaeger:latest