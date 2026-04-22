"""ZhipuAI ASR transcription service with retry."""
import time
import logging
import subprocess
from pathlib import Path

from zhipuai import ZhipuAI

import config

logger = logging.getLogger(__name__)


class ASRService:
    """Transcribes audio files using ZhipuAI GLM-ASR."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ZHIPU_API_KEY
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not configured")
        self.client = ZhipuAI(api_key=self.api_key)

    def transcribe(self, audio_path: str, max_retries: int = 3) -> dict:
        """Transcribe a single audio file.

        Returns: {"success": bool, "text": str, "error": str | None}
        """
        path = Path(audio_path)
        if not path.exists():
            return {"success": False, "text": "", "error": f"File not found: {audio_path}"}

        # Try direct transcription first; if format rejected, convert via ffmpeg
        result = self._transcribe_with_retry(str(path), max_retries)
        if result["success"]:
            return result

        # If format issue, try converting to wav
        if result.get("needs_conversion"):
            logger.info("Converting %s to WAV via ffmpeg", path.name)
            wav_path = self._convert_to_wav(path)
            if wav_path:
                result = self._transcribe_with_retry(str(wav_path), max_retries)
                # Clean up temp wav
                try:
                    wav_path.unlink()
                except Exception:
                    pass
                return result
            return {"success": False, "text": "", "error": "ffmpeg conversion failed"}

        return result

    def transcribe_long(self, audio_path: str, progress_callback=None) -> dict:
        """Transcribe long audio by segmenting into chunks.

        Returns: {"success": bool, "text": str, "segments": int, "error": str | None}
        """
        path = Path(audio_path)

        # Convert to wav first for reliable segmentation
        wav_path = self._convert_to_wav(path) if path.suffix.lower() != ".wav" else path
        if not wav_path:
            return {"success": False, "text": "", "segments": 0, "error": "ffmpeg conversion failed"}

        segments = self._segment_audio(wav_path)
        if not segments:
            return {"success": False, "text": "", "segments": 0, "error": "Audio segmentation failed"}

        texts = []
        for i, seg in enumerate(segments, 1):
            if progress_callback:
                progress_callback(i, len(segments))

            result = self._transcribe_with_retry(str(seg), max_retries=2)
            if result["success"]:
                texts.append(result["text"])
            else:
                logger.warning("Segment %d/%d failed: %s", i, len(segments), result["error"])
                texts.append("")

            # Clean up segment
            try:
                seg.unlink()
            except Exception:
                pass

        # Clean up temp wav
        if wav_path != path:
            try:
                wav_path.unlink()
            except Exception:
                pass

        full_text = " ".join(t for t in texts if t)
        return {
            "success": bool(full_text),
            "text": full_text,
            "segments": len(segments),
            "error": None if full_text else "All segments returned empty",
        }

    def _transcribe_with_retry(self, audio_path: str, max_retries: int = 3) -> dict:
        """Transcribe with exponential backoff retry."""
        last_error = None
        for attempt in range(max_retries):
            try:
                with open(audio_path, "rb") as f:
                    response = self.client.audio.transcriptions.create(
                        model=config.ASR_MODEL,
                        file=f,
                    )
                text = response.text if hasattr(response, "text") else str(response)
                if not text or not text.strip():
                    return {"success": False, "text": "", "error": "ASR returned empty text"}
                return {"success": True, "text": text.strip(), "error": None}
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                # Don't retry on auth/quota errors
                if any(kw in err_str for kw in ["auth", "unauthorized", "quota", "401", "403"]):
                    break
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 5
                    logger.warning("ASR attempt %d failed, retrying in %ds: %s", attempt + 1, wait, e)
                    time.sleep(wait)

        err_msg = str(last_error) if last_error else "Unknown error"
        needs_conv = any(kw in err_msg.lower() for kw in ["format", "unsupported", "decode", "invalid"])
        return {"success": False, "text": "", "error": f"ASR failed after {max_retries} retries: {err_msg}",
                "needs_conversion": needs_conv}

    def _convert_to_wav(self, audio_path: Path) -> Path | None:
        """Convert audio to 16kHz mono WAV using ffmpeg."""
        if not config.FFMPEG_PATH.exists():
            logger.error("ffmpeg not found at %s", config.FFMPEG_PATH)
            return None

        out_path = audio_path.parent / f"{audio_path.stem}_converted.wav"
        cmd = [
            str(config.FFMPEG_PATH),
            "-i", str(audio_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            "-y", str(out_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode == 0 and out_path.exists():
                return out_path
            logger.error("ffmpeg stderr: %s", result.stderr.decode(errors="replace")[:500])
            return None
        except Exception as e:
            logger.error("ffmpeg failed: %s", e)
            return None

    def _segment_audio(self, wav_path: Path, segment_sec: int = config.SEGMENT_DURATION) -> list[Path]:
        """Segment WAV into fixed-duration chunks."""
        if not config.FFMPEG_PATH.exists():
            return []

        out_dir = wav_path.parent / f"{wav_path.stem}_segments"
        out_dir.mkdir(exist_ok=True)

        cmd = [
            str(config.FFMPEG_PATH),
            "-i", str(wav_path),
            "-f", "segment",
            "-segment_time", str(segment_sec),
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            "-y", str(out_dir / "seg_%04d.wav"),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            if result.returncode != 0:
                logger.error("Segmentation failed: %s", result.stderr.decode(errors="replace")[:500])
                return []
            segments = sorted(out_dir.glob("seg_*.wav"))
            logger.info("Segmented into %d chunks", len(segments))
            return segments
        except Exception as e:
            logger.error("Segmentation error: %s", e)
            return []
