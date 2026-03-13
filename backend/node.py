import requests
import socket
import os
import threading

from peer_server import start_peer_server
from chunker import merge_chunks

TRACKER = "http://127.0.0.1:8000"

PEER_PORT = 9000


def join_network():

    r = requests.post(
        f"{TRACKER}/join",
        params={"ip": "127.0.0.1", "port": PEER_PORT}
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