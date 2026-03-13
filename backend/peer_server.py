import socket
import os

CHUNKS_DIR = "storage/chunks"


def start_peer_server(host="0.0.0.0", port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Peer server running on {port}")
    while True:
        conn, addr = server.accept()
        request = conn.recv(1024).decode()
        try:
            file_hash, chunk_id = request.split("|")
            path = os.path.join(CHUNKS_DIR, file_hash, f"chunk_{chunk_id}")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    conn.sendall(f.read())
        except:
            pass
        conn.close()