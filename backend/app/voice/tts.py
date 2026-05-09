"""
Text-to-Speech (TTS) module — defaults to local Kokoro-82M ONNX,
with Edge-TTS as a lightweight fallback.

Kokoro (r/LocalLLaMA favorite):
  - Model: hexgrad/Kokoro-82M  (Apache 2.0)
  - ONNX:  onnx-community/Kokoro-82M-v1.0-ONNX
  - 82M params, ~300 MB, real-time on CPU
  - Voices: am_adam (Jarvis), af_heart (Friday)

Edge-TTS (fallback):
  - Uses Microsoft Edge speech endpoints internally
  - No local model needed, works instantly
  - Voices: en-US-GuyNeural, en-GB-SoniaNeural
"""

from __future__ import annotations

import asyncio
import io
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

try:
    import sounddevice as sd
except OSError:
    sd = None  # PortAudio not available (e.g. CI runners)

logger = logging.getLogger("voice.tts")

# Default persona voices
JARVIS_VOICE = "am_adam"  # Kokoro male
FRIDAY_VOICE = "af_heart"  # Kokoro female


class TTSEngine:
    """TTS engine with Kokoro primary and Edge-TTS fallback."""

    def __init__(self, voice: str = JARVIS_VOICE):
        self.voice = voice
        self._kokoro = None
        self._kokoro_failed = False
        self._edge = None

    # ── Internal loaders ─────────────────────────────────────────────────────

    def _load_kokoro(self):
        if self._kokoro is not None:
            return
        try:
            from app.voice.kokoro_tts import KokoroTTSEngine

            self._kokoro = KokoroTTSEngine(voice=self.voice)
            logger.info("Kokoro TTS loaded (voice=%s).", self.voice)
        except Exception as exc:
            self._kokoro_failed = True
            logger.warning("Kokoro TTS failed to load (%s). Will use Edge-TTS fallback.", exc)

    def _load_edge(self):
        if self._edge is not None:
            return
        try:
            import edge_tts

            # Map Kokoro voice names to Edge voice names
            edge_voice = "en-US-GuyNeural" if self.voice.startswith("am_") else "en-GB-SoniaNeural"
            self._edge = edge_tts.Communicate("", edge_voice)
            logger.info("Edge-TTS fallback ready (voice=%s).", edge_voice)
        except Exception as exc:
            logger.warning("Edge-TTS also failed: %s", exc)

    # ── Public API ─────────────────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """Blocking: synthesize and play text."""
        logger.info("[TTS] %s", text[:120])

        # Try Kokoro first
        if not self._kokoro_failed:
            self._load_kokoro()
        if self._kokoro is not None:
            try:
                self._kokoro.speak(text)
                return
            except Exception as exc:
                logger.warning("Kokoro speak failed (%s), falling back to Edge-TTS.", exc)

        # Fallback: Edge-TTS
        self._edge_speak(text)

    async def text_to_speech(self, text: str, play: bool = True) -> bytes:
        """Async: synthesize text; optionally play. Returns audio bytes."""
        # Try Kokoro
        if not self._kokoro_failed:
            self._load_kokoro()
        if self._kokoro is not None:
            try:
                return await self._kokoro.text_to_speech(text, play=play)
            except Exception as exc:
                logger.warning("Kokoro async TTS failed (%s), using Edge-TTS fallback.", exc)

        # Fallback: Edge-TTS
        return await self._edge_text_to_speech(text, play=play)

    # ── Edge-TTS fallback implementation ───────────────────────────────────

    def _edge_speak(self, text: str) -> None:
        try:
            import edge_tts

            edge_voice = "en-US-GuyNeural" if self.voice.startswith("am_") else "en-GB-SoniaNeural"
            communicate = edge_tts.Communicate(text, edge_voice)
            mp3_bytes = b""
            import asyncio

            async def collect():
                nonlocal mp3_bytes
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        mp3_bytes += chunk["data"]

            asyncio.run(collect())
            self._play_mp3_bytes(mp3_bytes)
        except Exception as exc:
            logger.error("Edge-TTS fallback also failed: %s", exc)
            print(f"🗣  {text}")

    async def _edge_text_to_speech(self, text: str, play: bool = True) -> bytes:
        import edge_tts

        edge_voice = "en-US-GuyNeural" if self.voice.startswith("am_") else "en-GB-SoniaNeural"
        communicate = edge_tts.Communicate(text, edge_voice)
        mp3_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_bytes += chunk["data"]
        if play:
            await asyncio.to_thread(self._play_mp3_bytes, mp3_bytes)
        return mp3_bytes

    def _play_mp3_bytes(self, mp3_bytes: bytes) -> None:
        """Decode MP3 and play through speakers."""
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
            samples /= np.iinfo(np.int16).max
            if sd is not None:
                sd.play(samples, audio.frame_rate)
                sd.wait()
            else:
                logger.warning("PortAudio not available; skipping playback.")
        except Exception:
            logger.warning("pydub not available; using temp-file playback.")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(mp3_bytes)
                path = f.name
            try:
                subprocess.run(
                    [sys.executable, "-m", "edge_tts", "--play", path],
                    check=False,
                    capture_output=True,
                )
            finally:
                Path(path).unlink(missing_ok=True)


# ── Singleton ───────────────────────────────────────────────────────────────

_tts: TTSEngine | None = None


def get_tts_engine(voice: str | None = None) -> TTSEngine:
    global _tts
    if _tts is None:
        _tts = TTSEngine(voice=voice or JARVIS_VOICE)
    elif voice and _tts.voice != voice:
        _tts.voice = voice
    return _tts
