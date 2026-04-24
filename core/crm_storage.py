"""CRM database operations — reads/writes the shared help.db."""
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import config

logger = logging.getLogger(__name__)

STATUS_LABELS = {"open": "待处理", "in_progress": "处理中", "completed": "已完成", "cancelled": "已取消"}


class CRMDatabase:

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or str(config.DB_PATH)
        self._migrate()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _migrate(self):
        with self._conn() as conn:
            try:
                conn.execute("ALTER TABLE routing_history ADD COLUMN claude_analyzed INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

    # ── Task list ──────────────────────────────────────────────────────────

    def list_tasks(self, limit: int = 100, status: str = None, assignee: str = None) -> list[dict]:
        conditions = []
        params = []
        if status:
            conditions.append("r.status = ?")
            params.append(status)
        if assignee:
            conditions.append("r.assignee = ?")
            params.append(assignee)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(f"""
                SELECT r.*,
                       COUNT(DISTINCT n.id) AS note_count,
                       (SELECT image_path FROM task_attachments
                        WHERE routing_id = r.id LIMIT 1) AS first_image_path
                FROM routing_history r
                LEFT JOIN task_notes n ON n.routing_id = r.id
                {where}
                GROUP BY r.id
                ORDER BY r.created_at DESC
                LIMIT ?
            """, params).fetchall()
            return [dict(r) for r in rows]

    # ── Task detail ────────────────────────────────────────────────────────

    def get_task(self, routing_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM routing_history WHERE id = ?", (routing_id,)
            ).fetchone()
            if not row:
                return None
            task = dict(row)

            notes = conn.execute(
                "SELECT * FROM task_notes WHERE routing_id = ? ORDER BY created_at ASC",
                (routing_id,)
            ).fetchall()
            task["notes"] = [dict(n) for n in notes]

            attachments = conn.execute(
                "SELECT * FROM task_attachments WHERE routing_id = ?", (routing_id,)
            ).fetchall()
            task["attachments"] = [dict(a) for a in attachments]

            return task

    # ── Status update ──────────────────────────────────────────────────────

    def update_status(self, routing_id: int, new_status: str, updated_by: str) -> bool:
        now = datetime.now().isoformat()
        updates = {"status": new_status}
        if new_status == "in_progress":
            updates["accepted_by"] = updated_by
            updates["accepted_at"] = now
        elif new_status == "completed":
            updates["completed_at"] = now
            if not self._get_field(routing_id, "accepted_by"):
                updates["accepted_by"] = updated_by

        sets = ", ".join(f"{k} = ?" for k in updates)
        vals = list(updates.values()) + [routing_id]
        with self._conn() as conn:
            conn.execute(f"UPDATE routing_history SET {sets} WHERE id = ?", vals)
        logger.info("Task %d status → %s by %s", routing_id, new_status, updated_by)
        return True

    def _get_field(self, routing_id: int, field: str):
        with self._conn() as conn:
            row = conn.execute(f"SELECT {field} FROM routing_history WHERE id = ?", (routing_id,)).fetchone()
            return row[0] if row else None

    # ── Notes ──────────────────────────────────────────────────────────────

    def add_note(self, routing_id: int, note_text: str, note_by: str) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO task_notes (routing_id, note_text, note_by) VALUES (?, ?, ?)",
                (routing_id, note_text, note_by),
            )
            return cur.lastrowid

    # ── Claude analysis ────────────────────────────────────────────────────

    def list_unanalyzed_tasks(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, transcribed_text, image_context FROM routing_history "
                "WHERE COALESCE(claude_analyzed, 0) = 0 ORDER BY created_at ASC LIMIT 5"
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_claude_analyzed(self, routing_id: int, fields: dict):
        allowed = {"assignee", "department", "priority", "task_description", "reason"}
        updates = {k: v for k, v in fields.items() if k in allowed and v}
        updates["claude_analyzed"] = 1
        sets = ", ".join(f"{k} = ?" for k in updates)
        vals = list(updates.values()) + [routing_id]
        with self._conn() as conn:
            conn.execute(f"UPDATE routing_history SET {sets} WHERE id = ?", vals)

    # ── Delete ────────────────────────────────────────────────────────────

    def delete_task(self, routing_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM task_notes WHERE routing_id = ?", (routing_id,))
            conn.execute("DELETE FROM task_attachments WHERE routing_id = ?", (routing_id,))
            conn.execute("DELETE FROM routing_history WHERE id = ?", (routing_id,))
        logger.info("Task %d deleted", routing_id)

    # ── Stats ──────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT COALESCE(status, 'open') AS s, COUNT(*) AS c FROM routing_history GROUP BY s"
            ).fetchall()
        counts = {r["s"]: r["c"] for r in rows}
        return {
            "open": counts.get("open", 0),
            "in_progress": counts.get("in_progress", 0),
            "completed": counts.get("completed", 0),
            "total": sum(counts.values()),
        }
