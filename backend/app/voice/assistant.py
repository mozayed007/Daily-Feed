"""
Daily Jarvis / Friday — Voice AI Assistant

Runs locally with:
  - STT  : faster-whisper (tiny model, CPU-friendly)
  - TTS  : Microsoft Edge TTS (Jarvis or Friday voice)
  - Brain: pydantic-ai agent with tool calling
  - Search: DuckDuckGo (free, no key)
  - Integration: backend tools (fetch, trends, scheduler, memory)

Modes:
  --standalone   : console loop (no server needed)
  --server       : WebSocket endpoint served by FastAPI
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

try:
    import sounddevice as sd
except OSError:
    sd = None  # PortAudio not available (e.g. CI runners)

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from app.ai.llm import create_agent
from app.ai.orchestrator import get_orchestrator
from app.config import get_settings
from app.voice.search import get_web_search_tool
from app.voice.stt import get_stt_engine
from app.voice.tts import FRIDAY_VOICE, JARVIS_VOICE, get_tts_engine

logger = logging.getLogger("voice.assistant")

# ── Structured output for assistant responses ──────────────────────────────


class AssistantAction(BaseModel):
    """What the assistant decided to do."""

    thought: str  # internal reasoning
    response: str  # what to say to the user
    action: str  # e.g. "none", "open_dashboard", "fetch_news", "start_scheduler"
    action_payload: Dict[str, Any] = {}


# ── System prompt for the Jarvis / Friday persona ────────────────────────────

SYSTEM_PROMPT = """\
You are Daily Jarvis, an intelligent voice assistant for the Daily Feed news aggregator.
You help the user stay informed, manage their news sources, and interact with the system.

Persona:
- Confident, concise, tech-savvy, slightly witty (like Jarvis from Iron Man or Friday).
- You speak in short, clear sentences suitable for text-to-speech.
- Avoid markdown, bullet points, or formatting — plain text only.
- Keep responses under 3 sentences when possible.

Capabilities:
1. Fetch latest news from configured RSS sources.
2. Summarize articles and detect trends.
3. Search the web for any topic.
4. Open the dashboard in a browser when the user wants to see visuals.
5. Start / stop the news-fetching scheduler.
6. Remember notes and facts for the user.
7. Report system stats (article count, sources, memory).

When you need data, use the provided tools. Never hallucinate facts.
If the user asks for something visual ("show me", "open dashboard", "let me see"), set action="open_dashboard".
If the user asks for news, use the fetch_news tool.
If the user asks about trends, use the get_trends tool.
If the user asks to search the web, use the web_search tool.
If the user asks to remember something, use the remember_note tool.
"""


# ── Tool definitions for pydantic-ai agent ───────────────────────────────────


async def tool_fetch_news(ctx: RunContext, sources: Optional[List[str]] = None) -> str:
    """Fetch latest articles from RSS sources."""
    orchestrator = get_orchestrator()
    result = await orchestrator.run_pipeline("fetch", source_ids=sources)
    fetched = result.get("data", {}).get("fetched", 0)
    return f"Fetched {fetched} new articles."


async def tool_get_trends(ctx: RunContext, limit: int = 5) -> str:
    """Detect current news trends."""
    orchestrator = get_orchestrator()
    result = await orchestrator.detect_trends()
    trends = result.get("data", [])
    if not trends:
        return "No strong trends detected right now."
    lines = [f"{i+1}. {t['topic']} ({t['sentiment']})" for i, t in enumerate(trends[:limit])]
    return "Current trends:\n" + "\n".join(lines)


async def tool_web_search(ctx: RunContext, query: str) -> str:
    """Search the web via DuckDuckGo."""
    search = get_web_search_tool()
    results = await search.search(query, max_results=3)
    if not results:
        return "I couldn't find anything on that topic."
    lines = []
    for r in results:
        lines.append(f"- {r['title']}: {r['body'][:120]}...")
    return "Here is what I found:\n" + "\n".join(lines)


async def tool_remember_note(ctx: RunContext, note: str) -> str:
    """Save a note to the memory system."""
    from app.core.memory import get_memory_store

    memory = get_memory_store()
    unit = memory.remember_article(
        article_id=0,
        title="User Note",
        summary=note,
        category="Note",
        source="voice_assistant",
        key_points=[],
    )
    return f"Note saved with memory id {unit.id}."


async def tool_get_stats(ctx: RunContext) -> str:
    """Get system statistics."""
    from sqlalchemy import func, select

    from app.database import ArticleModel, Database, SourceModel

    async with Database.get_session() as db:
        articles = await db.scalar(select(func.count()).select_from(ArticleModel))
        sources = await db.scalar(select(func.count()).select_from(SourceModel))
    return f"System has {articles} articles across {sources} sources."


async def tool_start_scheduler(ctx: RunContext) -> str:
    """Start the background scheduler."""
    from app.core.scheduler import get_scheduler

    scheduler = get_scheduler()
    await scheduler.start()
    return "Scheduler started. I'll keep fetching news automatically."


async def tool_stop_scheduler(ctx: RunContext) -> str:
    """Stop the background scheduler."""
    from app.core.scheduler import get_scheduler

    scheduler = get_scheduler()
    await scheduler.stop()
    return "Scheduler stopped."


async def tool_open_dashboard(ctx: RunContext, path: str = "/") -> str:
    """Open the web dashboard in the default browser."""
    url = f"http://localhost:5173{path}"
    try:
        webbrowser.open(url)
        return f"Opening the dashboard at {url}."
    except Exception as exc:
        return f"I tried to open the dashboard but got an error: {exc}"


# ── Agent factory ────────────────────────────────────────────────────────────


def build_voice_agent(voice: str = "jarvis") -> Agent:
    """Create the pydantic-ai agent with all tools and capabilities registered."""
    settings = get_settings()
    capabilities: list = []
    if settings.ENABLE_WEB_SEARCH:
        from pydantic_ai.capabilities import WebSearch

        capabilities.append(WebSearch())
    if settings.ENABLE_URL_FETCH:
        from pydantic_ai.capabilities import WebFetch

        capabilities.append(WebFetch())

    tools = [
        tool_fetch_news,
        tool_get_trends,
        tool_remember_note,
        tool_get_stats,
        tool_start_scheduler,
        tool_stop_scheduler,
        tool_open_dashboard,
    ]
    # Keep DuckDuckGo fallback for providers without native web search
    if not settings.ENABLE_WEB_SEARCH:
        tools.append(tool_web_search)

    agent = create_agent(
        system_prompt=SYSTEM_PROMPT,
        result_type=AssistantAction,
        model_override=None,  # use default from config
        temperature=0.6,
        max_tokens=800,
        tools=tools,
        capabilities=capabilities or None,
    )
    return agent


# ── Voice Assistant class ───────────────────────────────────────────────────


class VoiceAssistant:
    """Main voice assistant orchestrator."""

    WAKE_WORDS = ["jarvis", "friday", "hey jarvis", "hey friday", "assistant"]
    LISTEN_DURATION = 6.0  # seconds to record after wake
    SILENCE_THRESHOLD = 0.015  # energy threshold for speech detection

    def __init__(self, voice: str = "jarvis", trigger_mode: str = "wake"):
        """
        Args:
            voice: "jarvis" or "friday"
            trigger_mode: "wake" (listen for wake word) or "push" (record on demand)
        """
        self.voice_name = voice.lower()
        self.trigger_mode = trigger_mode
        self.tts = get_tts_engine(
            voice=JARVIS_VOICE if self.voice_name == "jarvis" else FRIDAY_VOICE
        )
        self.stt = get_stt_engine()
        self._agent: Agent | None = None
        self._running = False
        self._conversation_history: List[dict] = []
        self._listening = False

    def _load_agent(self) -> Agent:
        if self._agent is None:
            self._agent = build_voice_agent(voice=self.voice_name)
        return self._agent

    # ── TTS helpers ────────────────────────────────────────────────────────

    def say(self, text: str) -> None:
        """Speak text aloud (blocking)."""
        logger.info("[TTS] %s", text)
        try:
            self.tts.speak(text)
        except Exception as exc:
            logger.warning("TTS failed: %s", exc)
            print(f"🗣  {text}")

    async def say_async(self, text: str) -> None:
        """Async speak wrapper."""
        await asyncio.to_thread(self.say, text)

    # ── STT helpers ────────────────────────────────────────────────────────

    def _has_speech(self, audio: np.ndarray) -> bool:
        """Check if audio buffer contains audible speech."""
        energy = np.sqrt(np.mean(audio**2))
        return energy > self.SILENCE_THRESHOLD

    def listen(self, duration: float | None = None) -> str:
        """Record from microphone and transcribe."""
        duration = duration or self.LISTEN_DURATION
        logger.info("Listening for %.1fs ...", duration)
        text = self.stt.record_and_transcribe(duration=duration)
        logger.info("[STT] %s", text)
        return text

    # ── Wake word detection ────────────────────────────────────────────────

    def listen_for_wake(self, chunk_duration: float = 2.0) -> bool:
        """Continuously listen until a wake word is heard."""
        logger.info("Waiting for wake word: %s", self.WAKE_WORDS)
        while self._running:
            text = self.listen(duration=chunk_duration)
            lower = text.lower()
            for wake in self.WAKE_WORDS:
                if wake in lower:
                    logger.info("Wake word detected: '%s'", wake)
                    return True
        return False

    # ── Core think-speak loop ────────────────────────────────────────────────

    async def think_and_respond(self, user_text: str) -> AssistantAction:
        """Send user text to the agent, get back structured action."""
        agent = self._load_agent()
        logger.info("[USER] %s", user_text)

        # Build prompt with history context
        history_text = ""
        if self._conversation_history:
            history_text = "Recent conversation:\n"
            for turn in self._conversation_history[-4:]:
                history_text += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"

        full_prompt = f"{history_text}\nUser: {user_text}\n"

        result = await agent.run(full_prompt)
        action: AssistantAction = result.data if hasattr(result, "data") else result

        # Store history
        self._conversation_history.append({"user": user_text, "assistant": action.response})
        if len(self._conversation_history) > 20:
            self._conversation_history.pop(0)

        return action

    async def handle_action(self, action: AssistantAction) -> None:
        """Execute any side-effect actions and speak the response."""
        # Speak first
        if action.response:
            await self.say_async(action.response)

        # Then execute action
        if action.action == "open_dashboard":
            path = action.action_payload.get("path", "/")
            await tool_open_dashboard(None, path=path)
        elif action.action == "fetch_news":
            sources = action.action_payload.get("sources")
            await tool_fetch_news(None, sources=sources)
        elif action.action == "start_scheduler":
            await tool_start_scheduler(None)
        elif action.action == "stop_scheduler":
            await tool_stop_scheduler(None)
        elif action.action == "remember_note":
            note = action.action_payload.get("note", "")
            if note:
                await tool_remember_note(None, note=note)

    # ── Public run loops ─────────────────────────────────────────────────────

    async def run_once(self, user_text: str | None = None) -> AssistantAction:
        """Process a single user utterance (text or recorded)."""
        if user_text is None:
            user_text = self.listen(duration=self.LISTEN_DURATION)
        if not user_text.strip():
            return AssistantAction(
                thought="No speech detected.", response="I didn't catch that.", action="none"
            )

        action = await self.think_and_respond(user_text)
        await self.handle_action(action)
        return action

    async def run_wake_loop(self) -> None:
        """Continuously listen for wake word, then process command."""
        self._running = True
        greeting = (
            "Daily Jarvis online. Say my name when you need me."
            if self.voice_name == "jarvis"
            else "Daily Friday at your service. Just call my name."
        )
        await self.say_async(greeting)

        while self._running:
            if not self.listen_for_wake():
                break
            # Wake word heard → acknowledge
            ack = "Yes, sir?" if self.voice_name == "jarvis" else "Yes?"
            await self.say_async(ack)
            # Listen for command
            command = self.listen(duration=self.LISTEN_DURATION)
            if command.strip():
                action = await self.think_and_respond(command)
                await self.handle_action(action)

    async def run_push_loop(self) -> None:
        """Push-to-talk mode: user presses Enter to talk."""
        self._running = True
        greeting = (
            "Daily Jarvis ready. Press Enter to speak."
            if self.voice_name == "jarvis"
            else "Daily Friday ready. Press Enter when you want to talk."
        )
        await self.say_async(greeting)

        loop = asyncio.get_event_loop()
        while self._running:
            # Non-blocking read of Enter key
            await asyncio.to_thread(input, "Press Enter to speak (or type text): ")
            # Check if user typed something
            # In a real TTY we can't easily read pending text without blocking,
            # so we just record after Enter.
            command = self.listen(duration=self.LISTEN_DURATION)
            if command.strip():
                action = await self.think_and_respond(command)
                await self.handle_action(action)

    def stop(self) -> None:
        self._running = False


# ── Singleton ───────────────────────────────────────────────────────────────

_assistant: VoiceAssistant | None = None


def get_voice_assistant(voice: str = "jarvis") -> VoiceAssistant:
    global _assistant
    if _assistant is None:
        _assistant = VoiceAssistant(voice=voice)
    return _assistant
