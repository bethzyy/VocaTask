"""SQLite database + audio file storage for Help app."""
import sqlite3
import uuid
import logging
from contextlib import contextmanager
from pathlib import Path

import config

logger = logging.getLogger(__name__)


class Database:
    """SQLite database with context manager pattern (from tailorCV)."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(config.DB_PATH)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_tables(self):
        with self._conn() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS transcription_jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'queued',
                audio_path TEXT NOT NULL,
                original_filename TEXT,
                duration_seconds REAL,
                text_result TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS routing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_path TEXT,
                transcribed_text TEXT,
                task_description TEXT,
                priority TEXT,
                department TEXT,
                assignee TEXT,
                reason TEXT,
                method TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

    # --- Transcription Jobs ---

    def create_job(self, audio_path: str, filename: str) -> str:
        job_id = uuid.uuid4().hex[:12]
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO transcription_jobs (job_id, status, audio_path, original_filename) VALUES (?, 'queued', ?, ?)",
                (job_id, audio_path, filename),
            )
        return job_id

    def get_job(self, job_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM transcription_jobs WHERE job_id = ?", (job_id,)).fetchone()
            return dict(row) if row else None

    def update_job(self, job_id: str, **kwargs):
        if not kwargs:
            return
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        vals = list(kwargs.values()) + [job_id]
        with self._conn() as conn:
            conn.execute(f"UPDATE transcription_jobs SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?", vals)

    def get_queued_job(self) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM transcription_jobs WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    def list_jobs(self, limit: int = 50) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM transcription_jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # --- Routing History ---

    def save_routing(self, audio_path: str, text: str, routing: dict):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO routing_history
                   (audio_path, transcribed_text, task_description, priority, department, assignee, reason, method)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (audio_path, text, routing.get("task_description"), routing.get("priority"),
                 routing.get("department"), routing.get("assignee"), routing.get("reason"), routing.get("method")),
            )

    def list_routing_history(self, limit: int = 50) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM routing_history ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]


class AudioStorage:
    """Manages audio file saving and retrieval."""

    def save(self, file_obj, original_filename: str) -> dict:
        ext = Path(original_filename).suffix.lower()
        if ext not in config.SUPPORTED_AUDIO_EXT:
            ext = ".webm"

        file_id = uuid.uuid4().hex[:12]
        filename = f"{file_id}{ext}"
        filepath = config.AUDIO_DIR / filename

        file_obj.save(str(filepath))
        size = filepath.stat().st_size

        logger.info("Saved audio: %s (%d bytes)", filename, size)
        return {
            "file_id": file_id,
            "file_path": str(filepath),
            "filename": filename,
            "size_bytes": size,
        }

    def get_path(self, file_id: str) -> Path | None:
        for f in config.AUDIO_DIR.iterdir():
            if f.stem.startswith(file_id):
                return f
        return None

    @staticmethod
    def validate(file_obj) -> tuple[bool, str]:
        if not file_obj or not file_obj.filename:
            return False, "No file provided"

        ext = Path(file_obj.filename).suffix.lower()
        if ext not in config.SUPPORTED_AUDIO_EXT:
            return False, f"Unsupported format: {ext}. Supported: {', '.join(config.SUPPORTED_AUDIO_EXT)}"

        file_obj.seek(0, 2)
        size = file_obj.tell()
        file_obj.seek(0)

        max_bytes = config.MAX_AUDIO_SIZE_MB * 1024 * 1024
        if size > max_bytes:
            return False, f"File too large: {size / 1024 / 1024:.1f}MB (max {config.MAX_AUDIO_SIZE_MB}MB)"

        return True, ""
