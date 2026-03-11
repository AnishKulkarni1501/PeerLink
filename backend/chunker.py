import os
import hashlib

CHUNK_SIZE = 512 * 1024  # 512KB

def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def split_file(path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    chunks = []
    with open(path, "rb") as f:
        i = 0
        while True:
            data = f.read(CHUNK_SIZE)
            if not data:
                break
            chunk_path = os.path.join(out_dir, f"chunk_{i}")
            with open(chunk_path, "wb") as cf:
                cf.write(data)
            chunks.append(chunk_path)
            i += 1
    return chunks

def merge_chunks(chunks, out_path):
    with open(out_path, "wb") as out:
        for c in chunks:
            with open(c, "rb") as f:
                out.write(f.read())