# eros

Eros is locally hosted Multiagent that plans date ideas for lovers, friends and groups

requesting Alloc: salloc -p students --time=03:00:00 --cpus-per-task=16 --mem=110G --gres=gpu:2
running only ollama: sbatch start_ollama.sh

tunneling: ssh -L 11434:localhost:11434 -J joostadrian@nickel.fhgr.ch joostadrian@nickel

resolve dns manually: nslookup nickel.fhgr.ch

start tool inspector: npx @modelcontextprotocol/inspector (nvm use 23.11.0)

start server: uvicorn server:app --reload --port 8080
