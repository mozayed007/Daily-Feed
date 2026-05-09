"""
Speech-to-Text (STT) module using faster-whisper + Distil-Whisper.

Distil-Whisper is the r/LocalLLaMA favorite:
  - Model: distil-whisper/distil-large-v3 (Apache 2.0)
  - 49% faster than Whisper large-v3, 1% WER difference
  - Works via faster-whisper CTranslate2 engine
  - Runs 100% local, no cloud needed

We default to distil-large-v3 for quality, with tiny as CPU-constrained fallback.
"""
from __future__ import annotations

import io
import logging
import tempfile
from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

logger = logging.getLogger("voice.stt")

# Default: distil-large-v3 (r/LocalLLaMA recommendation)
# Fallback: tiny (if VRAM/RAM is very constrained)
DEFAULT_MODEL = "distil-large-v3"
FALLBACK_MODEL = "tiny"


class STTEngine:
    """Local faster-whisper STT engine with Distil-Whisper support."""

    def __init__(self, model_size: str = DEFAULT_MODEL, device: str = "auto", compute_type: str = "int8"):
        self.model_size = model_size
        self._model: WhisperModel | None = None
        self._device = device
        self._compute_type = compute_type
        self._fallback = False

    def load(self) -> None:
        if self._model is not None:
            return
        try:
            logger.info(
                "Loading faster-whisper model '%s' (device=%s, compute=%s) ...",
                self.model_size, self._device, self._compute_type,
            )
            self._model = WhisperModel(
                self.model_size,
                device=self._device,
                compute_type=self._compute_type,
                download_root=None,  # use HF cache
            )
            logger.info("STT model loaded (%s).", self.model_size)
        except Exception as exc:
            if self.model_size != FALLBACK_MODEL:
                logger.warning(
                    "Failed to load %s (%s), falling back to %s.",
                    self.model_size, exc, FALLBACK_MODEL,
                )
                self.model_size = FALLBACK_MODEL
                self._fallback = True
                self._model = WhisperModel(
                    FALLBACK_MODEL,
                    device=self._device,
                    compute_type=self._compute_type,
                )
                logger.info("STT fallback model loaded (%s).", FALLBACK_MODEL)
            else:
                raise

    def unload(self) -> None:
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("STT model unloaded.")

    def _is_loaded(self) -> bool:
        return self._model is not None

    def transcribe_audio(self, audio_np: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe a numpy audio buffer (float32, [-1, 1])."""
        if not self._is_loaded():
            self.load()

        # Write temporary WAV
        import wave
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            w = wave.open(f.name, "wb")
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            data = (audio_np * 32767).astype(np.int16)
            w.writeframes(data.tobytes())
            w.close()
            path = f.name

        try:
            segments, info = self._model.transcribe(
                path,
                language="en",
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=True,
            )
            text = " ".join([seg.text for seg in segments]).strip()
            logger.debug("Transcribed (%s, %s): %s", info.language, info.language_probability, text)
            return text
        finally:
            Path(path).unlink(missing_ok=True)

    def record_and_transcribe(self, duration: float = 5.0, samplerate: int = 16000) -> str:
        """Record audio from the default microphone and transcribe."""
        logger.info("Recording %.1f seconds ...", duration)
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="float32")
        sd.wait()
        audio_1d = audio.reshape(-1)
        return self.transcribe_audio(audio_1d, samplerate)


# Singleton
_stt: STTEngine | None = None


def get_stt_engine(model_size: str | None = None) -> STTEngine:
    global _stt
    if _stt is None:
        _stt = STTEngine(model_size=model_size or DEFAULT_MODEL)
    elif model_size and _stt.model_size != model_size:
        _stt.model_size = model_size
        _stt.unload()
    return _stt
