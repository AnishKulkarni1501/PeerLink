from fastapi import FastAPI, UploadFile, File
from tracker import add_file, get_peers, list_files
from chunker import hash_file, split_file
import os

app = FastAPI()

SHARED_DIR = "storage/shared"
CHUNKS_DIR = "storage/chunks"
os.makedirs(SHARED_DIR, exist_ok=True)
os.makedirs(CHUNKS_DIR, exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/share")
async def share_file(peer_id: str, file: UploadFile = File(...)):
    file_path = os.path.join(SHARED_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    file_hash = hash_file(file_path)
    split_file(file_path, os.path.join(CHUNKS_DIR, file_hash))
    add_file(peer_id, file_hash)

    return {"file_hash": file_hash}

@app.get("/files")
def files():
    return {"files": list_files()}

@app.get("/peers/{file_hash}")
def peers(file_hash: str):
    return {"peers": get_peers(file_hash)}