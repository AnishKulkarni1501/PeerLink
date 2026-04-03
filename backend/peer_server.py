import os
import socket
import threading
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [peer] %(message)s")

CHUNKS_DIR = os.path.realpath("storage/chunks")  # Resolve once at startup


def _send_error(conn: socket.socket, message: str):
    try:
        conn.sendall(f"ERR {message}".encode())
    except OSError:
        pass


def handle_client(conn: socket.socket, addr):
    try:
        raw = conn.recv(1024).decode(errors="replace").strip()

        parts = raw.split("|")
        if len(parts) != 2:
            _send_error(conn, "invalid request — expected <hash>|<chunk_id>")
            return

        file_hash, chunk_id = parts
        #Is SHA256?:
        if not (len(file_hash) == 64 and all(c in "0123456789abcdef" for c in file_hash)):
            _send_error(conn, "invalid file_hash")
            return

        # chunk_id must be a non-negative integer
        if not chunk_id.isdigit():
            _send_error(conn, "invalid chunk_id")
            return

        #
        candidate = os.path.realpath(
            os.path.join(CHUNKS_DIR, file_hash, f"chunk_{chunk_id}")
        )

        #must still be inside CHUNKS_DIR
        if not candidate.startswith(CHUNKS_DIR + os.sep):
            logging.warning("Path traversal attempt from %s: %s", addr, raw)
            _send_error(conn, "forbidden")
            return

    
        if not os.path.isfile(candidate):
            _send_error(conn, "not found")
            return

        with open(candidate, "rb") as f:
            conn.sendall(f.read())

        logging.info("Served %s chunk %s to %s", file_hash[:8], chunk_id, addr)

    except Exception as exc:
        logging.exception("Unhandled error for %s: %s", addr, exc)
    finally:
        conn.close()


def start_peer_server(host: str = "0.0.0.0", port: int = 9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(10)
    logging.info("Peer server listening on %s:%d", host, port)

    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()
