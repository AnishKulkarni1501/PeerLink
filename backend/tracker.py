# Simple in-memory tracker
file_peers = {}   # file_hash -> set(peer_id)
peer_files = {}   # peer_id -> set(file_hash)
file_metadata = {}

def register_peer(peer_id: str):
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

def get_peers(file_hash: str):
    return list(file_peers.get(file_hash, []))

def list_files():
    return list(file_peers.keys())