# PeerLink : A Peer to Peer File Distribution System
<p> Uses FastAPI as backend and ASP.NET for frontend</p>

<h1>Backend</h1><hr><br>


## 🏗️ Architecture


### Components

**Tracker (FastAPI)**
- Handles peer discovery, metadata management, and node liveness  
- Does not store or transfer file data  

**Nodes (Peers)**
- Act as both clients and servers  
- Exchange file chunks directly via TCP  

### Communication Flow

- Control Plane → HTTP (via Tracker)  
- Data Plane → Peer-to-Peer TCP  

---

## How It Works

### Seeding

1. File is hashed using SHA-256 → `file_hash`  
2. File is split into 512 KB chunks  
3. Each chunk is hashed individually  
4. Chunks are stored locally:

5. File metadata is announced to the tracker  
6. Node begins serving chunks  

---

### Downloading

1. Fetch metadata and peer list from tracker  
2. Download chunks in parallel (round-robin strategy)  
3. Verify each chunk using SHA-256  
4. Reassemble chunks in correct order  
5. Verify final file integrity  

---

## Peer Lifecycle

- Joins via `/join`  
- Heartbeat every ~60 seconds  
- Peers removed after ~120 seconds of inactivity  
- State persisted in SQLite  

---

## Key Features

- Distributed peer-to-peer file transfer  
- Chunk-based parallel downloads  
- Integrity verification using SHA-256  
- Fault-tolerant peer discovery  
- Lightweight tracker (no data storage)


# How to use:
- Run node.py on backend and tracker.py on any system you want the tracker to be.
- node.py has a simple GUI that you can use for downloading/seeding.


# Frontend
- TODO.