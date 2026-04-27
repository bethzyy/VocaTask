"""VocaTask — Voice Task Routing & Transcription. Flask entry point."""
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from flask import Flask, jsonify, request, render_template

import config
from core.storage import AudioStorage, Database, ImageStorage
from core.asr import ASRService
from core.router import TaskRouter
from core.vision import VisionService
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
app.config["MAX_CONTENT_LENGTH"] = (config.MAX_AUDIO_SIZE_MB + config.MAX_IMAGE_SIZE_MB * config.MAX_IMAGES_PER_TASK) * 1024 * 1024

audio_storage = AudioStorage()
image_storage = ImageStorage()
db = Database()
asr_service = ASRService()
task_router = TaskRouter()
vision_service = VisionService()
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
        return None, ({"success": False, "error": f"Save failed: {e}"}, 500)


def _save_and_validate_images():
    """Validate and save uploaded images. Returns (list_of_saved, error_or_none)."""
    files = request.files.getlist("images")
    if not files or all(f.filename == "" for f in files):
        return [], None

    if len(files) > config.MAX_IMAGES_PER_TASK:
        return [], ({"success": False, "error": f"Too many images (max {config.MAX_IMAGES_PER_TASK})"}, 400)

    saved_images = []
    for f in files:
        if f.filename == "":
            continue
        ok, err = ImageStorage.validate(f)
        if not ok:
            return [], ({"success": False, "error": err}, 400)
        try:
            saved = image_storage.save(f, f.filename)
            saved["original_filename"] = f.filename
            saved_images.append(saved)
        except Exception as e:
            return [], ({"success": False, "error": f"Save failed: {e}"}, 500)

    return saved_images, None


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
    """One-step: audio (+ images) → transcribe → describe images → route."""
    # 1. Audio is required
    saved, err = _save_and_validate()
    if err:
        return jsonify(err[0]), err[1]

    # 2. Images are optional
    saved_images, img_err = _save_and_validate_images()
    if img_err:
        return jsonify(img_err[0]), img_err[1]

    # 3+4. Concurrently: transcribe audio AND describe all images (they are independent)
    with ThreadPoolExecutor(max_workers=1 + len(saved_images)) as pool:
        asr_future = pool.submit(asr_service.transcribe, saved["file_path"])
        vision_futures = {
            pool.submit(vision_service.describe, img["file_path"]): img
            for img in saved_images
        }

        asr_result = asr_future.result()
        if not asr_result["success"]:
            return jsonify({"success": False, "transcription": asr_result,
                            "routing": {}, "error": asr_result["error"]})

        image_descriptions = []
        for fut, img in vision_futures.items():
            desc_result = fut.result()
            if desc_result["success"]:
                img["description"] = desc_result["description"]
                image_descriptions.append(desc_result["description"])
            else:
                img["description"] = f"(图片描述失败: {desc_result['error']})"

    image_context = (
        "\n".join(f"图片{i+1}: {d}" for i, d in enumerate(image_descriptions))
        if image_descriptions else None
    )

    # 5. Route with combined context (needs both ASR + Vision results)
    route_result = task_router.route(asr_result["text"], image_context=image_context)

    # 6. Save to history
    routing_id = db.save_routing(saved["file_path"], asr_result["text"], route_result.get("routing", {}), image_context=image_context)
    if saved_images:
        db.save_attachments(routing_id, saved_images)

    return jsonify({
        "success": True,
        "transcription": {"text": asr_result["text"]},
        "image_descriptions": image_descriptions,
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


# ========== Image Serving ==========

@app.route("/api/images/<file_id>")
def serve_image(file_id):
    """Serve a stored image file."""
    from flask import send_file
    path = image_storage.get_path(file_id)
    if not path or not path.exists():
        return "", 404
    return send_file(str(path))


# ========== Main ==========

if __name__ == "__main__":
    queue_worker.start()
    logger.info("Help app starting on https://localhost:%d", config.PORT)
    try:
        app.run(host=config.HOST, port=config.PORT, debug=True, threaded=True, ssl_context="adhoc")
    finally:
        queue_worker.stop()
