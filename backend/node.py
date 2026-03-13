import requests
import socket
import os
import threading

from peer_server import start_peer_server
from chunker import merge_chunks

import socket
import requests

TRACKER = "http://192.168.1.40:8000"   # tracker machine
PEER_PORT = 9000


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def join_network():

    ip = get_local_ip()

    r = requests.post(
        f"{TRACKER}/join",
        params={
            "ip": ip,
            "port": PEER_PORT
        }
    )

    return r.json()["peer_id"]
def download_file(file_hash):

    meta = requests.get(
        f"{TRACKER}/metadata/{file_hash}"
    ).json()

    total_chunks = meta["total_chunks"]
    filename = meta["filename"]

    peers = requests.get(
        f"{TRACKER}/peers/{file_hash}"
    ).json()["peers"]

    os.makedirs(f"downloads/{file_hash}", exist_ok=True)

    for i in range(total_chunks):

        peer = peers[0]
        s = socket.socket()
        s.connect((peer["ip"], peer["port"]))
        s.send(f"{file_hash}|{i}".encode())

        data = b""

        while True:
            part = s.recv(4096)
            if not part:
                break
            data += part

        s.close()

        with open(f"downloads/{file_hash}/chunk_{i}", "wb") as f:
            f.write(data)
        print("Downloaded chunk", i)

    chunks = [
        f"downloads/{file_hash}/chunk_{i}"
        for i in range(total_chunks)
    ]

    merge_chunks(chunks, f"downloads/{filename}")
    print("File reconstructed:", filename)


def main():

    peer_id = join_network()

    print("Peer ID:", peer_id)

    threading.Thread(
        target=start_peer_server,
        args=("0.0.0.0", PEER_PORT),
        daemon=True
    ).start()

    while True:

        cmd = input("Enter file hash to download: ")

        if cmd:

            download_file(cmd)


if __name__ == "__main__":
    main()