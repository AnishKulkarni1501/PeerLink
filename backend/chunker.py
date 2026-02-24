file_peers = {}   
peer_files = {}   

def register_peer(peer_id: str):
    if peer_id not in peer_files:
        peer_files[peer_id] = set()

def add_file(peer_id: str, file_hash: str):
    register_peer(peer_id)

    peer_files[peer_id].add(file_hash)
    if file_hash not in file_peers:
        file_peers[file_hash] = set()
    file_peers[file_hash].add(peer_id)

def get_peers(file_hash: str):
    return list(file_peers.get(file_hash, []))

def list_files():
    return list(file_peers.keys())

