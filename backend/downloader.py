import socket
import os
import requests

PEER_IP = "127.0.0.1"
PEER_PORT = 9000

FILE_HASH = input("File Hash: ")
metadata = requests.get(f"http://localhost:8000/metadata/{FILE_HASH}").json()

total_chunks = metadata["total_chunks"]
filename = metadata["filename"]

DOWNLOAD_DIR = "storage/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

for i in range(total_chunks):

    s = socket.socket()
    s.connect((PEER_IP, PEER_PORT))

    request = f"{FILE_HASH}|{i}"
    s.send(request.encode())

    chunk_data = b""

    while True:
        data = s.recv(4096)
        if not data:
            break
        chunk_data += data

    s.close()

    with open(f"{DOWNLOAD_DIR}/chunk_{i}", "wb") as f:
        f.write(chunk_data)

    print(f"Downloaded chunk {i}")

print("Download finished")