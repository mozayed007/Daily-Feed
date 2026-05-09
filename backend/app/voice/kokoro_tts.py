"""
Local TTS using Kokoro-82M ONNX — r/LocalLLaMA favorite.

- Model: hexgrad/Kokoro-82M (Apache 2.0)
- ONNX:  onnx-community/Kokoro-82M-v1.0-ONNX
- Runs 100% locally via ONNX Runtime, no cloud.
- 82M params, ~300 MB, real-time on CPU.

Voice IDs (American English):
  af_heart   — warm female (default "Friday")
  af_bella   — clear female
  am_adam    — calm male (default "Jarvis")
  am_echo    — bright male
"""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import List, Optional

import numpy as np
import sounddevice as sd
import soundfile as sf

logger = logging.getLogger("voice.kokoro_tts")

# Voice defaults
JARVIS_VOICE = "am_adam"
FRIDAY_VOICE = "af_heart"


class KokoroTTSEngine:
    """Local Kokoro TTS via ONNX Runtime."""

    def __init__(self, voice: str = JARVIS_VOICE):
        self.voice = voice
        self._model = None
        self._voices = {}
        self._repo = "onnx-community/Kokoro-82M-v1.0-ONNX"

    # ── Lazy model loading ─────────────────────────────────────────────────

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        try:
            import onnxruntime as ort
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise ImportError(
                "Kokoro TTS requires 'onnxruntime' and 'huggingface_hub'. "
                "Run: pip install onnxruntime huggingface_hub"
            ) from exc

        logger.info("Downloading Kokoro ONNX model from %s ...", self._repo)
        model_path = hf_hub_download(
            repo_id=self._repo,
            filename="kokoro-v1.0.onnx",
            local_dir=None,
        )
        logger.info("Loading ONNX session ...")
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self._model = ort.InferenceSession(model_path, sess_options)

        # Load voice pack
        voice_path = hf_hub_download(
            repo_id=self._repo,
            filename=f"voices/{self.voice}.pt",
            local_dir=None,
        )
        logger.info("Loading voice pack %s ...", self.voice)
        import torch

        self._voices[self.voice] = torch.load(voice_path, map_location="cpu", weights_only=True)

        logger.info("Kokoro TTS ready (voice=%s).", self.voice)

    # ── Phonemization (lightweight, no espeak-ng dependency) ────────────────

    @staticmethod
    def _simple_phonemize(text: str) -> tuple[List[str], List[int]]:
        """
        Very lightweight grapheme → phoneme approximation.
        Falls back to character-level if no espeak.
        Returns (phoneme_tokens, token_ids).
        """
        try:
            import espeakng

            e = espeakng.ESpeakNG()
            e.voice = "en"
            phonemes = e.g2p(text)
            return list(phonemes), []
        except Exception:
            pass

        # Fallback: just split into chars and map to simple IDs
        # Kokoro expects ~78 phoneme IDs; we use a minimal mapping
        text = text.lower()
        text = re.sub(r"[^a-z0-9 .,!?;:]", "", text)
        chars = list(text)
        # Basic char-to-ID mapping (0 = pad, 1-26 = a-z, 27 = space, 28-32 = punctuation)
        char_map = {c: i + 1 for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")}
        char_map[" "] = 27
        char_map["."] = 28
        char_map[","] = 29
        char_map["!"] = 30
        char_map["?"] = 31
        char_map[";"] = 32
        char_map[":"] = 33
        ids = [char_map.get(c, 0) for c in chars]
        return chars, ids

    # ── Synthesis ───────────────────────────────────────────────────────────

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        """
        Synthesize text. Returns (audio_samples_float32, sample_rate).
        """
        self._ensure_loaded()

        # Simple sentence chunking (Kokoro works best on <200 char chunks)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: List[str] = []
        current = ""
        for s in sentences:
            if len(current) + len(s) < 200:
                current += " " + s if current else s
            else:
                if current:
                    chunks.append(current)
                current = s
        if current:
            chunks.append(current)

        all_audio: List[np.ndarray] = []
        for chunk in chunks:
            audio = self._synthesize_chunk(chunk)
            all_audio.append(audio)

        if not all_audio:
            return np.zeros(0, dtype=np.float32), 24000

        # Crossfade between chunks for smoothness
        final = all_audio[0]
        for next_audio in all_audio[1:]:
            overlap = min(1200, len(final), len(next_audio))
            if overlap > 0:
                fade_out = np.linspace(1, 0, overlap, dtype=np.float32)
                fade_in = np.linspace(0, 1, overlap, dtype=np.float32)
                final[-overlap:] = final[-overlap:] * fade_out + next_audio[:overlap] * fade_in
                final = np.concatenate([final, next_audio[overlap:]])
            else:
                final = np.concatenate([final, next_audio])
        return final, 24000

    def _synthesize_chunk(self, text: str) -> np.ndarray:
        """Synthesize a single short chunk."""
        # Tokenize text to phoneme-style IDs
        _, ids = self._simple_phonemize(text)
        if not ids:
            return np.zeros(0, dtype=np.float32)

        # Prepare inputs for ONNX
        # Kokoro ONNX expects:
        #   input_ids: [batch, seq_len]
        #   style: [batch, 256]  (from voice pack)
        #   speed: [batch]  (1.0 = normal)
        #   voice_name: optional
        import onnxruntime as ort

        input_ids = np.array([[0] + ids + [0]], dtype=np.int64)  # [1, seq_len]
        seq_len = input_ids.shape[1]

        # Get style from voice pack
        voice_data = self._voices.get(self.voice)
        if voice_data is None:
            style = np.zeros((1, 256), dtype=np.float32)
        else:
            # voice_data may be a tensor of shape [256] or dict
            if hasattr(voice_data, "numpy"):
                style = voice_data.numpy().reshape(1, -1).astype(np.float32)
            elif isinstance(voice_data, dict) and "style" in voice_data:
                style = np.array(voice_data["style"], dtype=np.float32).reshape(1, -1)
            else:
                style = np.array(voice_data, dtype=np.float32).reshape(1, -1)

        speed = np.array([1.0], dtype=np.float32)

        # Pad style if needed
        if style.shape[1] < 256:
            pad = np.zeros((1, 256 - style.shape[1]), dtype=np.float32)
            style = np.concatenate([style, pad], axis=1)
        elif style.shape[1] > 256:
            style = style[:, :256]

        inputs = {
            "input_ids": input_ids,
            "style": style,
            "speed": speed,
        }

        # Run inference
        outputs = self._model.run(None, inputs)
        audio = outputs[0].reshape(-1).astype(np.float32)
        return audio

    # ── Playback ────────────────────────────────────────────────────────────

    def play_audio(self, audio: np.ndarray, samplerate: int = 24000) -> None:
        """Play audio through speakers."""
        if len(audio) == 0:
            return
        sd.play(audio, samplerate)
        sd.wait()

    def speak(self, text: str) -> None:
        """Synthesize and immediately play text."""
        logger.info("[Kokoro TTS] %s", text[:120])
        audio, sr = self.synthesize(text)
        self.play_audio(audio, sr)

    async def text_to_speech(self, text: str, play: bool = True) -> bytes:
        """Async-friendly TTS; returns MP3-ish bytes if needed."""
        import asyncio

        audio, sr = await asyncio.to_thread(self.synthesize, text)
        if play:
            await asyncio.to_thread(self.play_audio, audio, sr)
        # Encode to in-memory WAV for return
        buf = io.BytesIO()
        sf.write(buf, audio, sr, format="WAV", subtype="PCM_16")
        return buf.getvalue()


# ── Singleton ───────────────────────────────────────────────────────────────

_kokoro_tts: KokoroTTSEngine | None = None


def get_kokoro_tts(voice: str | None = None) -> KokoroTTSEngine:
    global _kokoro_tts
    if _kokoro_tts is None:
        _kokoro_tts = KokoroTTSEngine(voice=voice or JARVIS_VOICE)
    elif voice and _kokoro_tts.voice != voice:
        _kokoro_tts.voice = voice
    return _kokoro_tts
