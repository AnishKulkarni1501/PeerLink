import hashlib
import os

CHUNK_SIZE = 512 * 1024  # 512 KB (CAN BE MODIFIED)


def hash_file(path: str) -> str:
    """Return the SHA-256 hex digest of the entire file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(8192)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def split_file(path: str, out_dir: str) -> list[dict]:
    """
    Split *path* into 512 KB chunks stored under *out_dir*.

    Returns a list of dicts, one per chunk:
        {
            "index":  int,        # 0-based position
            "path":   str,        # absolute path to the chunk file
            "hash":   str,        # SHA-256 hex digest of this chunk
        }

    Storing per-chunk hashes lets receivers verify each chunk
    independently instead of only checking the whole file at the end.
    """
    os.makedirs(out_dir, exist_ok=True)
    chunks = []

    with open(path, "rb") as f:
        index = 0
        while True:
            data = f.read(CHUNK_SIZE)
            if not data:
                break

            chunk_hash = hashlib.sha256(data).hexdigest()
            chunk_path = os.path.join(out_dir, f"chunk_{index}")

            with open(chunk_path, "wb") as cf:
                cf.write(data)

            chunks.append({"index": index, "path": chunk_path, "hash": chunk_hash})
            index += 1

    return chunks


def verify_chunk(data: bytes, expected_hash: str) -> bool:
    #ret true if match.
    return hashlib.sha256(data).hexdigest() == expected_hash


def merge_chunks(chunk_dir: str, total_chunks: int, out_file: str):
    with open(out_file, "wb") as out:
        for i in range(total_chunks):
            chunk_path = os.path.join(chunk_dir, f"chunk_{i}")
            if not os.path.isfile(chunk_path):
                raise FileNotFoundError(
                    f"Missing chunk {i} — cannot merge incomplete file"
                )
            with open(chunk_path, "rb") as cf:
                out.write(cf.read())
