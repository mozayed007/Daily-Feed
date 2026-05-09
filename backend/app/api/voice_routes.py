"""
Voice Assistant API Routes

Provides:
- REST endpoints to control the assistant (start, stop, speak, status)
- WebSocket /ws/voice for real-time audio streaming (frontend companion)
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.voice.assistant import get_voice_assistant, AssistantAction
from app.voice.stt import get_stt_engine
from app.voice.tts import get_tts_engine

logger = logging.getLogger(__name__)
router = APIRouter()


# ── REST control endpoints ────────────────────────────────────────────────────

class SpeakRequest(BaseModel):
    text: str
    voice: Optional[str] = "jarvis"


class CommandRequest(BaseModel):
    text: str
    voice: Optional[str] = "jarvis"


@router.post("/voice/speak")
async def speak_text(request: SpeakRequest):
    """Speak text aloud via TTS."""
    tts = get_tts_engine(voice=request.voice)
    try:
        await tts.text_to_speech(request.text, play=True)
        return {"success": True, "message": "Spoken"}
    except Exception as exc:
        logger.error("TTS error: %s", exc)
        return {"success": False, "error": str(exc)}


@router.post("/voice/command")
async def run_text_command(request: CommandRequest):
    """Process a text command through the voice assistant brain (no mic needed)."""
    assistant = get_voice_assistant(voice=request.voice)
    try:
        action = await assistant.run_once(user_text=request.text)
        return {
            "success": True,
            "thought": action.thought,
            "response": action.response,
            "action": action.action,
            "action_payload": action.action_payload,
        }
    except Exception as exc:
        logger.error("Voice command error: %s", exc)
        return {"success": False, "error": str(exc)}


@router.get("/voice/status")
async def voice_status():
    """Get voice assistant status."""
    assistant = get_voice_assistant()
    return {
        "running": assistant._running,
        "voice": assistant.voice_name,
        "trigger_mode": assistant.trigger_mode,
        "history_turns": len(assistant._conversation_history),
    }


@router.post("/voice/stop")
async def stop_voice():
    """Stop any active voice loop."""
    assistant = get_voice_assistant()
    assistant.stop()
    return {"success": True, "message": "Voice assistant stopped"}


# ── WebSocket real-time endpoint ─────────────────────────────────────────────

class VoiceWebSocketManager:
    """Manages active WebSocket connections for voice streaming."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("Voice WS connected: %s", client_id)

    def disconnect(self, client_id: str) -> None:
        self.active_connections.pop(client_id, None)
        logger.info("Voice WS disconnected: %s", client_id)

    async def send_json(self, client_id: str, data: dict) -> None:
        ws = self.active_connections.get(client_id)
        if ws:
            await ws.send_json(data)


_ws_manager = VoiceWebSocketManager()


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """
    Real-time voice WebSocket.

    Protocol:
    Client -> Server : { "type": "audio", "data": "base64_pcm..." }
    Server -> Client : { "type": "transcription", "text": "..." }
    Server -> Client : { "type": "response", "text": "...", "action": "..." }
    Server -> Client : { "type": "audio", "data": "base64_mp3..." }   (optional TTS stream back)
    """
    client_id = f"voice_{id(websocket)}"
    await _ws_manager.connect(client_id, websocket)

    stt = get_stt_engine()
    assistant = get_voice_assistant()
    tts = get_tts_engine()

    try:
        while True:
            message = await websocket.receive_text()
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = payload.get("type")

            if msg_type == "audio":
                # Client sent base64-encoded audio (PCM float32 mono)
                audio_b64 = payload.get("data", "")
                try:
                    audio_bytes = base64.b64decode(audio_b64)
                    audio_np = np.frombuffer(audio_bytes, dtype=np.float32)
                except Exception as exc:
                    await websocket.send_json({"type": "error", "message": f"Audio decode error: {exc}"})
                    continue

                # Transcribe
                text = stt.transcribe_audio(audio_np, sample_rate=payload.get("sample_rate", 16000))
                await websocket.send_json({"type": "transcription", "text": text})

                if not text.strip():
                    continue

                # Think & respond
                action = await assistant.think_and_respond(text)
                await websocket.send_json({
                    "type": "response",
                    "text": action.response,
                    "action": action.action,
                    "action_payload": action.action_payload,
                })

                # If assistant wants to speak back, generate TTS audio and send
                if action.response:
                    try:
                        mp3_bytes = await tts.text_to_speech(action.response, play=False)
                        audio_b64_out = base64.b64encode(mp3_bytes).decode("utf-8")
                        await websocket.send_json({
                            "type": "audio",
                            "format": "mp3",
                            "data": audio_b64_out,
                        })
                    except Exception as exc:
                        logger.warning("TTS stream back failed: %s", exc)

                # Execute side-effect action
                await assistant.handle_action(action)

            elif msg_type == "text":
                # Client sent text directly (e.g. from a text input)
                text = payload.get("text", "")
                action = await assistant.think_and_respond(text)
                await websocket.send_json({
                    "type": "response",
                    "text": action.response,
                    "action": action.action,
                    "action_payload": action.action_payload,
                })
                if action.response:
                    try:
                        mp3_bytes = await tts.text_to_speech(action.response, play=False)
                        audio_b64_out = base64.b64encode(mp3_bytes).decode("utf-8")
                        await websocket.send_json({
                            "type": "audio",
                            "format": "mp3",
                            "data": audio_b64_out,
                        })
                    except Exception as exc:
                        logger.warning("TTS stream back failed: %s", exc)
                await assistant.handle_action(action)

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("Voice WS client %s disconnected", client_id)
    finally:
        _ws_manager.disconnect(client_id)
