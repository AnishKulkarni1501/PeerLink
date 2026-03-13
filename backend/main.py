from fastapi import FastAPI
from tracker import (
    register_peer,
    add_file,
    get_peers,
    get_metadata,
    list_files,
    list_peers
)

import uuid

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/join")
def join(ip: str, port: int):

    peer_id = str(uuid.uuid4())

    register_peer(peer_id, ip, port)

    return {"peer_id": peer_id}


@app.get("/peerlist")
def peerlist():
    return {"peers": list_peers()}


@app.get("/files")
def files():
    return {"files": list_files()}


@app.get("/peers/{file_hash}")
def peers(file_hash: str):
    return {"peers": get_peers(file_hash)}


@app.get("/metadata/{file_hash}")
def metadata(file_hash: str):
    return get_metadata(file_hash)