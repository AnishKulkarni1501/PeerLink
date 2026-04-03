import asyncio
import uuid

from fastapi import FastAPI, Request, HTTPException
from tracker import (
    register_peer,
    update_last_seen,
    evict_stale_peers,
    add_file,
    get_peers,
    get_metadata,
    list_files,
    list_peers,
)

app = FastAPI()

# ---------------------------------------------------------------------------
# Background task:   evict peers that stopped sending heartbeats
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def start_cleanup_task():
    async def _cleanup_loop():
        while True:
            evict_stale_peers(max_age_seconds=120)
            await asyncio.sleep(30)

    asyncio.create_task(_cleanup_loop())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/join")
def join(request: Request, port: int):
    ip = request.client.host
    peer_id = str(uuid.uuid4())
    register_peer(peer_id, ip, port)
    return {"peer_id": peer_id}


@app.post("/heartbeat")
def heartbeat(peer_id: str):
    update_last_seen(peer_id)
    return {"status": "ok"}


@app.post("/announce")
def announce(peer_id: str, file_hash: str, filename: str, total_chunks: int):
    add_file(peer_id, file_hash, filename, total_chunks)
    return {"status": "ok"}


@app.get("/peerlist")
def peerlist():
    return {"peers": list_peers()}


@app.get("/files")
def files():
    return {"files": list_files()}


@app.get("/peers/{file_hash}")
def peers(file_hash: str):
    result = get_peers(file_hash)
    if not result:
        raise HTTPException(status_code=404, detail="No peers found for this file")
    return {"peers": result}


@app.get("/metadata/{file_hash}")
def metadata(file_hash: str):
    result = get_metadata(file_hash)
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    return result
