import sqlite3
from contextlib import contextmanager
from .config import settings

DB_PATH = settings.data_path / "knowledge.sqlite3"


@contextmanager
def connect():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        yield con
        con.commit()
    finally:
        con.close()


def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_type TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)


def get_document(url):
    with connect() as con:
        row = con.execute(
            "SELECT * FROM documents WHERE url = ?", (url,)
        ).fetchone()
        return dict(row) if row else None


def save_document(url, title, digest, content, summary):
    with connect() as con:
        con.execute("""
        INSERT INTO documents(url,title,content_hash,content,summary)
        VALUES(?,?,?,?,?)
        ON CONFLICT(url) DO UPDATE SET
            title=excluded.title,
            content_hash=excluded.content_hash,
            content=excluded.content,
            summary=excluded.summary,
            fetched_at=CURRENT_TIMESTAMP
        """, (url, title, digest, content, summary))


def log_job(job_type, status, message=""):
    with connect() as con:
        con.execute(
            "INSERT INTO jobs(job_type,status,message) VALUES(?,?,?)",
            (job_type, status, message[:4000])
        )


def list_documents(limit=50):
    with connect() as con:
        rows = con.execute("""
        SELECT id,url,title,summary,fetched_at
        FROM documents
        ORDER BY fetched_at DESC
        LIMIT ?
        """, (min(max(limit, 1), 100),)).fetchall()
        return [dict(r) for r in rows]


def stats():
    with connect() as con:
        docs = con.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0]
        jobs = con.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0]
        return {"documents": docs, "jobs": jobs}