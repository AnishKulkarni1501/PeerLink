import socket
import os

HOST = "0.0.0.0"
PORT = 9000
CHUNKS_DIR = "storage/chunks"

def start_peer_server():
    s = socket.socket()
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"Peer server listening on {PORT}")

    while True:
        conn, addr = s.accept()
        data = conn.recv(1024).decode()
        file_hash, chunk_id = data.split("|")

        chunk_path = os.path.join(CHUNKS_DIR, file_hash, f"chunk_{chunk_id}")
        if os.path.exists(chunk_path):
            with open(chunk_path, "rb") as f:
                conn.sendall(f.read())
        conn.close()

if __name__ == "__main__":
    start_peer_server()