file_peers = {}
peer_files = {}
file_metadata = {}
peer_register = {}

def register_peer(peer_id, ip, port):

    peer_register[peer_id] = {
        "ip": ip,
        "port": port
    }

    if peer_id not in peer_files:
        peer_files[peer_id] = set()


def add_file(peer_id, file_hash, filename, total_chunks):
    if peer_id not in peer_files:
        peer_files[peer_id] = set()

    peer_files[peer_id].add(file_hash)

    if file_hash not in file_peers:
        file_peers[file_hash] = set()

    file_peers[file_hash].add(peer_id)

    file_metadata[file_hash] = {
        "filename": filename,
        "total_chunks": total_chunks
    }


def get_metadata(file_hash):
    return file_metadata.get(file_hash, {})


def get_peers(file_hash):

    peers = file_peers.get(file_hash, [])
    result = []
    for peer_id in peers:

        if peer_id in peer_register:

            info = peer_register[peer_id]

            result.append({
                "peer_id": peer_id,
                "ip": info["ip"],
                "port": info["port"]
            })

    return result


def list_files():
    return list(file_peers.keys())


def list_peers():
    return list(peer_register.keys())