"""VocaTask — Voice Task Routing & Transcription. Flask entry point."""
import logging
from datetime import datetime

from flask import Flask, jsonify, request, render_template

import config
from core.storage import AudioStorage, Database
from core.asr import ASRService
from core.router import TaskRouter
from core.queue import TranscriptionQueue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

config.ensure_dirs()

app = Flask(
    __name__,
    template_folder="web",
    static_folder="web/static",
)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_AUDIO_SIZE_MB * 1024 * 1024

audio_storage = AudioStorage()
db = Database()
asr_service = ASRService()
task_router = TaskRouter()
queue_worker = TranscriptionQueue(db, asr_service)


def _save_and_validate():
    """Common: validate and save uploaded audio. Returns saved dict or (error_dict, status)."""
    if "audio" not in request.files:
        return None, ({"success": False, "error": "No audio file in request"}, 400)

    file = request.files["audio"]
    ok, err = AudioStorage.validate(file)
    if not ok:
        return None, ({"success": False, "error": err}, 400)

    try:
        saved = audio_storage.save(file, file.filename)
        return saved, None
    except Exception as e:
        return None, ({"success": False, "error": f"Save failed: {e}"}), 500


# ========== Pages ==========

@app.route("/")
def index():
    return render_template("index.html")


# ========== Health ==========

@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
        "api_key_configured": bool(config.ZHIPU_API_KEY),
    })


@app.route("/favicon.ico")
def favicon():
    return "", 204


# ========== Workflow A: Quick Task ==========

@app.route("/api/upload-audio", methods=["POST"])
def upload_audio():
    saved, err = _save_and_validate()
    if err:
        return jsonify(err[0]), err[1]
    return jsonify({"success": True, **saved})


@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    saved, err = _save_and_validate()
    if err:
        return jsonify(err[0]), err[1]
    result = asr_service.transcribe(saved["file_path"])
    return jsonify({"success": result["success"], **saved, "transcription": result})


@app.route("/api/route", methods=["POST"])
def route_task():
    data = request.get_json(silent=True)
    if not data or not data.get("text"):
        return jsonify({"success": False, "error": "Missing 'text' field"}), 400
    result = task_router.route(data["text"])
    return jsonify(result)


@app.route("/api/transcribe-and-route", methods=["POST"])
def transcribe_and_route():
    """One-step: audio → transcribe → route."""
    saved, err = _save_and_validate()
    if err:
        return jsonify(err[0]), err[1]

    asr_result = asr_service.transcribe(saved["file_path"])
    if not asr_result["success"]:
        return jsonify({"success": False, "transcription": asr_result, "routing": {}, "error": asr_result["error"]})

    route_result = task_router.route(asr_result["text"])

    # Save to history
    db.save_routing(saved["file_path"], asr_result["text"], route_result.get("routing", {}))

    return jsonify({
        "success": True,
        "transcription": {"text": asr_result["text"]},
        "routing": route_result.get("routing", {}),
        "error": route_result.get("error"),
    })


# ========== Workflow B: Long-Form Transcription ==========

@app.route("/api/queue", methods=["POST"])
def queue_audio():
    """Upload long audio and queue for background processing."""
    saved, err = _save_and_validate()
    if err:
        return jsonify(err[0]), err[1]

    job_id = db.create_job(saved["file_path"], saved["filename"])
    return jsonify({"success": True, "job_id": job_id, "status": "queued"})


@app.route("/api/queue/status/<job_id>")
def queue_status(job_id):
    job = db.get_job(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404

    progress = queue_worker.get_progress(job_id)
    resp = {"success": True, "job_id": job_id, "status": job["status"], "progress": progress}

    if job["status"] == "completed" and job["text_result"]:
        resp["result"] = job["text_result"]
    elif job["status"] == "failed" and job["error_message"]:
        resp["error"] = job["error_message"]

    return jsonify(resp)


@app.route("/api/queue/results")
def queue_results():
    jobs = db.list_jobs(limit=50)
    return jsonify({"success": True, "jobs": jobs})


# ========== History ==========

@app.route("/api/history")
def history():
    routes = db.list_routing_history(limit=30)
    jobs = db.list_jobs(limit=30)
    return jsonify({"success": True, "routings": routes, "transcriptions": jobs})


# ========== Main ==========

if __name__ == "__main__":
    queue_worker.start()
    logger.info("Help app starting on http://localhost:%d", config.PORT)
    try:
        app.run(host=config.HOST, port=config.PORT, debug=True, threaded=True)
    finally:
        queue_worker.stop()
