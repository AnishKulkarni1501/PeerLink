import os
import socket
import threading
import time
import hashlib
import requests

from concurrent.futures import ThreadPoolExecutor, as_completed

from peer_server import start_peer_server
from chunker import merge_chunks, split_file, hash_file, verify_chunk

TRACKER   = "http://192.168.1.40:8000" # my own local ip
PEER_PORT = 9000

CHUNKS_DIR   = "storage/chunks"   # files this node is seeding
DOWNLOAD_DIR = "downloads"

# How many chunks to fetch simultaneously from different peers:
MAX_PARALLEL_DOWNLOADS = 4


# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def join_network() -> str:
    r = requests.post(
        f"{TRACKER}/join",
        params={"port": PEER_PORT},   
        timeout=5,
    )
    r.raise_for_status()
    return r.json()["peer_id"]


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

def _heartbeat_loop(peer_id: str, interval: int = 60):
    while True:
        try:
            requests.post(
                f"{TRACKER}/heartbeat",
                params={"peer_id": peer_id},
                timeout=5,
            )
        except requests.RequestException as e:
            print(f"[heartbeat] warning: {e}")
        time.sleep(interval)


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

def seed_file(peer_id: str, file_path: str):

    file_hash = hash_file(file_path)
    out_dir   = os.path.join(CHUNKS_DIR, file_hash)
    chunks    = split_file(file_path, out_dir)

    requests.post(
        f"{TRACKER}/announce",
        params={
            "peer_id":      peer_id,
            "file_hash":    file_hash,
            "filename":     os.path.basename(file_path),
            "total_chunks": len(chunks),
        },
        timeout=5,
    ).raise_for_status()

    print(f"[seed] Announced {os.path.basename(file_path)} ({len(chunks)} chunks) — hash: {file_hash}")
    return file_hash


# ---------------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------------

def _fetch_chunk(peer: dict, file_hash: str, chunk_index: int, expected_hash: str) -> bytes:
   
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#TCP
    s.settimeout(10)                 

    try:
        s.connect((peer["ip"], peer["port"]))
        s.sendall(f"{file_hash}|{chunk_index}\n".encode())

        data = b""
        while True:
            part = s.recv(4096)
            if not part:
                break
            data += part
    finally:
        s.close()

    #err  on failing.
    if data[:4] == b"ERR ":
        raise ValueError(f"Peer returned error: {data.decode(errors='replace')}")

    if not verify_chunk(data, expected_hash):
        raise ValueError(
            f"Integrity check failed for chunk {chunk_index} "
            f"(got {hashlib.sha256(data).hexdigest()[:12]}…)"
        )

    return data


def download_file(file_hash: str, chunk_hashes: list[str]):
    meta = requests.get(f"{TRACKER}/metadata/{file_hash}", timeout=5).json()
    total_chunks = meta["total_chunks"]
    filename     = meta["filename"]

    peers = requests.get(f"{TRACKER}/peers/{file_hash}", timeout=5).json()["peers"]
    if not peers:
        raise RuntimeError(f"No peers available for {file_hash}")

    chunk_dir = os.path.join(DOWNLOAD_DIR, file_hash)
    os.makedirs(chunk_dir, exist_ok=True)

    # ROUND Robin based downloaing.
    failed = []

    def _download_one(i: int):
        # Round-robin peer selection: chunk i goes to peers[i % len(peers)]
        # This spreads load across all available peers automatically.
        peer = peers[i % len(peers)]
        data = _fetch_chunk(peer, file_hash, i, chunk_hashes[i])
        path = os.path.join(chunk_dir, f"chunk_{i}")
        with open(path, "wb") as f:
            f.write(data)
        print(f"[download] chunk {i}/{total_chunks - 1} OK from {peer['ip']}")

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as pool:
        futures = {pool.submit(_download_one, i): i for i in range(total_chunks)}
        for future in as_completed(futures):
            i = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[download] chunk {i} FAILED: {e}")
                failed.append(i)

    if failed:
        raise RuntimeError(
            f"Download incomplete — {len(failed)} chunk(s) failed: {failed}"
        )

    # Merge file
    out_path = os.path.join(DOWNLOAD_DIR, filename)
    merge_chunks(chunk_dir, total_chunks, out_path)

    actual_hash = hash_file(out_path)
    if actual_hash != file_hash:
        os.remove(out_path)
        raise ValueError(
            f"Final file hash mismatch! Expected {file_hash}, got {actual_hash}. "
            f"File removed."
        )

    print(f"[download] '{filename}' reconstructed and verified.")
    return out_path


# ---------------------------------------------------------------------------
# on bash terminal
# ---------------------------------------------------------------------------

def main():
    peer_id = join_network()
    print(f"[node] Joined network — peer_id: {peer_id}")

    # Start serving chunks to other peers
    threading.Thread(
        target=start_peer_server,
        args=("0.0.0.0", PEER_PORT),
        daemon=True,
    ).start()
    print(f"[node] Peer server running on port {PEER_PORT}")

    # Start sending heartbeats so the tracker doesn't evict us!!
    threading.Thread(
        target=_heartbeat_loop,
        args=(peer_id,),
        daemon=True,
    ).start()
    print("[node] Heartbeat thread started")

    # Simple REPL
    print("\nCommands:  download <hash>   |   seed <filepath>   |   quit\n")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[node] Shutting down.")
            break

        if not line:
            continue

        parts = line.split(maxsplit=1)
        cmd   = parts[0].lower()

        if cmd == "quit":
            break
        
        elif cmd == "seed" and len(parts) == 2:
            
            path = parts[1].strip().strip('"').strip("'") #For full system paths.
            path = os.path.normpath(path)
            if not os.path.isfile(path):
                print(f"[seed] File not found: {path}")
            else:
                try:
                    seed_file(peer_id, path)
                except Exception as e:
                    print(f"[seed] Error: {e}")

        elif cmd == "seed" and len(parts) == 1:
            print("Seed WHAT? ;)")

        elif cmd == "download" and len(parts) == 1:
            print("Download WHAT? ;)")

        elif cmd == "download" and len(parts) == 2:
            fhash = parts[1]
            print("[download] Fetching chunk hashes from tracker metadata…")
            try:
                download_file(fhash, chunk_hashes=[])
            except Exception as e:
                print(f"[download] Error: either the file doesn't exist or you have the incorrect hash")

        else:
            print("Unknown command. Use:  download <hash>  |  seed <filepath>  |  quit")


if __name__ == "__main__":
    main()
