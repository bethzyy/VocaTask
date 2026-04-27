"""VocaTask CRM — Task management dashboard. Independent Flask service on port 8011."""
import logging
import threading
import time
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

import config
from core.crm_storage import CRMDatabase
from core.storage import ImageStorage
from core import ai_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

config.ensure_dirs()

app = Flask(
    __name__,
    template_folder="web/crm",
    static_folder="web/static",
)
CORS(app)

db = CRMDatabase()
image_storage = ImageStorage()


# ── AI Background Worker ────────────────────────────────────────────────

def _ai_worker():
    """Poll for unanalyzed tasks every 8 s.

    Only enriches tasks that lack assignee/department (i.e. main router failed).
    Never overwrites fields already set by the main routing pipeline.
    """
    while True:
        try:
            tasks = db.list_unanalyzed_tasks()
            for task in tasks:
                # Skip if already routed by main pipeline
                if task.get("assignee") and task.get("department"):
                    db.mark_claude_analyzed(task["id"], {})
                    logger.info("Task %d already routed, marking as analyzed", task["id"])
                    continue

                # Main router failed — use AI to fill in missing fields
                result = ai_router.analyze(
                    task.get("transcribed_text", ""),
                    task.get("image_context"),
                )
                db.mark_claude_analyzed(task["id"], result or {})
                if result:
                    logger.info("AI enriched unrouted task %d → %s / %s",
                                task["id"], result.get("assignee"), result.get("priority"))
        except Exception as e:
            logger.error("AI worker error: %s", e)
        time.sleep(8)


threading.Thread(target=_ai_worker, daemon=True, name="AIWorker").start()


# ── Pages ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


# ── API ────────────────────────────────────────────────────────────────────

@app.route("/api/crm/health")
def health():
    return jsonify({"status": "healthy", "service": "crm", "port": config.CRM_PORT})


@app.route("/api/crm/stats")
def stats():
    return jsonify({"success": True, "stats": db.get_stats()})


@app.route("/api/crm/tasks")
def list_tasks():
    status = request.args.get("status") or None
    assignee = request.args.get("assignee") or None
    tasks = db.list_tasks(limit=200, status=status, assignee=assignee)
    return jsonify({"success": True, "tasks": tasks})


@app.route("/api/crm/tasks/<int:task_id>")
def get_task(task_id):
    task = db.get_task(task_id)
    if not task:
        return jsonify({"success": False, "error": "Task not found"}), 404
    return jsonify({"success": True, "task": task})


@app.route("/api/crm/tasks/<int:task_id>/status", methods=["POST"])
def update_status(task_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    updated_by = data.get("updated_by", "").strip()
    if new_status not in ("open", "in_progress", "completed", "cancelled"):
        return jsonify({"success": False, "error": "Invalid status"}), 400
    if not updated_by:
        return jsonify({"success": False, "error": "updated_by is required"}), 400
    db.update_status(task_id, new_status, updated_by)
    return jsonify({"success": True})


@app.route("/api/images/<file_id>")
def serve_image(file_id):
    from flask import send_file
    path = image_storage.get_path(file_id)
    if not path or not path.exists():
        return "", 404
    return send_file(str(path))


@app.route("/api/crm/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    db.delete_task(task_id)
    return jsonify({"success": True})


@app.route("/api/crm/tasks/<int:task_id>/notes", methods=["POST"])
def add_note(task_id):
    data = request.get_json(silent=True) or {}
    note_text = (data.get("note_text") or "").strip()
    note_by = (data.get("note_by") or "").strip()
    if not note_text or not note_by:
        return jsonify({"success": False, "error": "note_text and note_by are required"}), 400
    note_id = db.add_note(task_id, note_text, note_by)
    return jsonify({"success": True, "note_id": note_id})


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("CRM service starting on http://localhost:%d", config.CRM_PORT)
    app.run(host=config.HOST, port=config.CRM_PORT, debug=True, threaded=True)
