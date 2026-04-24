"""Background worker for long-form audio transcription."""
import threading
import time
import logging
from datetime import datetime

from core.storage import Database
from core.asr import ASRService

logger = logging.getLogger(__name__)


class TranscriptionQueue:
    """Background thread that processes queued transcription jobs."""

    def __init__(self, db: Database, asr: ASRService):
        self.db = db
        self.asr = asr
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._current_progress: dict = {}

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Transcription queue worker started")

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Transcription queue worker stopped")

    def _loop(self):
        while not self._stop.is_set():
            job = self.db.get_queued_job()
            if job:
                self._process(job)
            else:
                self._stop.wait(5)

    def _process(self, job: dict):
        job_id = job["job_id"]
        audio_path = job["audio_path"]
        logger.info("Processing job %s: %s", job_id, audio_path)

        self.db.update_job(job_id, status="processing")
        self._current_progress = {"job_id": job_id, "current": 0, "total": 0}

        def on_progress(current, total):
            self._current_progress = {"job_id": job_id, "current": current, "total": total}
            self.db.update_job(job_id, duration_seconds=current * 25)

        try:
            result = self.asr.transcribe_long(audio_path, progress_callback=on_progress)
            if result["success"]:
                self.db.update_job(job_id, status="completed", text_result=result["text"],
                                   completed_at=datetime.now().isoformat())
                logger.info("Job %s completed: %d segments", job_id, result.get("segments", 0))
            else:
                self.db.update_job(job_id, status="failed", error_message=result.get("error", "Unknown error"))
                logger.error("Job %s failed: %s", job_id, result.get("error"))
        except Exception as e:
            self.db.update_job(job_id, status="failed", error_message=str(e))
            logger.exception("Job %s crashed", job_id)
        finally:
            self._current_progress = {}

    def get_progress(self, job_id: str) -> str:
        """Get human-readable progress for a job."""
        if self._current_progress.get("job_id") == job_id:
            c = self._current_progress["current"]
            t = self._current_progress["total"]
            if t > 0:
                return f"处理中... {c}/{t} 片段"
        return ""
