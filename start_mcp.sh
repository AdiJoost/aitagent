#!/bin/bash

HOST_IP=$(ip route get 1 | awk '{print $7; exit}')
AITAGENT_DIR="$(cd "$(dirname "$0")"; pwd)"

echo "=== MCP Debug Start ==="
echo "Host IP: $HOST_IP"
echo "AITAGENT_DIR: $AITAGENT_DIR"

echo ""
echo "Starting ait-mcp in foreground (logs visible)..."
apptainer exec \
  --env-file "$AITAGENT_DIR/.env" \
  --pwd /ait-mcp \
  ait-mcp.sif \
  python -m uvicorn run:app --host 0.0.0.0 --port 8000 &

MCP_PID=$!

echo "ait-mcp PID: $MCP_PID"
echo ""
echo "Waiting 5 seconds for startup..."
sleep 5

echo ""
echo "=== Connection Tests ==="

echo ""
echo "1) curl http://localhost:8000/ (root)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/ || echo "FAILED: localhost:8000"

echo ""
echo "2) curl http://localhost:8000/mcp (MCP endpoint - POST)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' http://localhost:8000/mcp || echo "FAILED: localhost:8000/mcp"

echo ""
echo "3) curl http://${HOST_IP}:8000/ (host IP - root)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://${HOST_IP}:8000/ || echo "FAILED: ${HOST_IP}:8000"

echo ""
echo "4) curl http://${HOST_IP}:8000/mcp (host IP - MCP endpoint - POST)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' http://${HOST_IP}:8000/mcp || echo "FAILED: ${HOST_IP}:8000/mcp"

echo ""
echo "5) ss -tlnp | grep 8000 (check port binding)"
ss -tlnp | grep 8000 || echo "Port 8000 not found in listening sockets"

echo ""
echo "6) Full response from MCP endpoint:"
curl -s -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' http://localhost:8000/mcp

echo ""
echo ""
echo "=== Done. Stopping MCP (PID $MCP_PID) ==="
sleep 60
kill $MCP_PID 2>/dev/null
wait $MCP_PID 2>/dev/null
echo "Stopped."
