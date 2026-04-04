import sqlite3
import datetime

DB_PATH = "tracker.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS peers (
                peer_id   TEXT PRIMARY KEY,
                ip        TEXT NOT NULL,
                port      INTEGER NOT NULL,
                last_seen TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS files (
                file_hash    TEXT NOT NULL,
                peer_id      TEXT NOT NULL,
                filename     TEXT NOT NULL,
                total_chunks INTEGER NOT NULL,
                PRIMARY KEY (file_hash, peer_id),
                FOREIGN KEY (peer_id) REFERENCES peers(peer_id) ON DELETE CASCADE
            )
        """)


# Call once at startup
init_db()


def _now() -> str:
    return datetime.datetime.utcnow().isoformat()


def register_peer(peer_id: str, ip: str, port: int):
    with get_db() as db:
        db.execute(
            """
            INSERT INTO peers (peer_id, ip, port, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(peer_id) DO UPDATE SET
                ip        = excluded.ip,
                port      = excluded.port,
                last_seen = excluded.last_seen
            """,
            (peer_id, ip, port, _now()),
        )


def update_last_seen(peer_id: str):
    with get_db() as db:
        db.execute(
            "UPDATE peers SET last_seen = ? WHERE peer_id = ?",
            (_now(), peer_id),
        )


def evict_stale_peers(max_age_seconds: int = 120):#remove if not active > 120 sec....
    cutoff = (
        datetime.datetime.utcnow() - datetime.timedelta(seconds=max_age_seconds)
    ).isoformat()
    with get_db() as db:
        db.execute("DELETE FROM peers WHERE last_seen < ?", (cutoff,))


def add_file(peer_id: str, file_hash: str, filename: str, total_chunks: int):
    with get_db() as db:
        db.execute(
            """
            INSERT INTO files (file_hash, peer_id, filename, total_chunks)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(file_hash, peer_id) DO UPDATE SET
                filename     = excluded.filename,
                total_chunks = excluded.total_chunks
            """,
            (file_hash, peer_id, filename, total_chunks),
        )


def get_metadata(file_hash: str) -> dict:
    with get_db() as db:
        row = db.execute(
            """
            SELECT filename, total_chunks FROM files 
            WHERE file_hash = ? 
            AND peer_id IN (SELECT peer_id FROM peers)
            LIMIT 1
            """,
            (file_hash,),
        ).fetchone()
    return dict(row) if row else {}


def get_peers(file_hash: str) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            """
            SELECT p.peer_id, p.ip, p.port
            FROM files f
            JOIN peers p ON p.peer_id = f.peer_id
            WHERE f.file_hash = ?
            """,
            (file_hash,),
        ).fetchall()
    return [dict(r) for r in rows]


def list_files() -> list[str]:
    with get_db() as db:
        rows = db.execute("SELECT DISTINCT file_hash FROM files").fetchall()
    return [r["file_hash"] for r in rows]


def list_peers() -> list[str]:
    with get_db() as db:
        rows = db.execute("SELECT peer_id FROM peers").fetchall()
    return [r["peer_id"] for r in rows]
