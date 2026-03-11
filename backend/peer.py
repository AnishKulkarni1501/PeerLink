import socket
import os

HOST = "0.0.0.0"
PORT = 9000

CHUNKS_DIR = "storage/chunks"

def start_peer_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Peer server listening on port {PORT}")

    while True:
        conn, addr = server.accept()
        print("Connection from", addr)

        request = conn.recv(1024).decode()
        print("Request:", request)

        try:
            file_hash, chunk_id = request.split("|")
            chunk_path = os.path.join(CHUNKS_DIR, file_hash, f"chunk_{chunk_id}")

            if os.path.exists(chunk_path):
                with open(chunk_path, "rb") as f:
                    conn.sendall(f.read())
            else:
                conn.sendall(b"ERROR: chunk not found")

        except Exception as e:
            conn.sendall(str(e).encode())

        conn.close()

if __name__ == "__main__":
    start_peer_server()