#!/usr/bin/env python3
"""
Daily Jarvis / Friday — Standalone Voice Assistant

Usage:
    python voice_assistant.py               # wake-word mode (Jarvis)
    python voice_assistant.py --friday      # wake-word mode (Friday)
    python voice_assistant.py --push        # push-to-talk mode
    python voice_assistant.py --once        # single command then exit

Environment:
    Requires backend dependencies installed (see requirements.txt).
    Microphone + speakers needed for voice interaction.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent))

from app.voice.assistant import VoiceAssistant
from app.core.logging_config import configure_logging

configure_logging()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily Jarvis / Friday Voice Assistant")
    parser.add_argument("--friday", action="store_true", help="Use Friday persona (female voice)")
    parser.add_argument("--push", action="store_true", help="Push-to-talk mode instead of wake-word")
    parser.add_argument("--once", action="store_true", help="Run a single command and exit")
    parser.add_argument("--text", type=str, default=None, help="Text command to run (implies --once)")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    voice = "friday" if args.friday else "jarvis"
    mode = "push" if args.push else "wake"

    assistant = VoiceAssistant(voice=voice, trigger_mode=mode)

    if args.text:
        print(f"🎙  [{voice.upper()}] Running: {args.text}")
        action = await assistant.run_once(user_text=args.text)
        print(f"🤖  {action.response}")
        if action.action != "none":
            print(f"⚡  Action: {action.action} → {action.action_payload}")
        return

    if args.once:
        print(f"🎙  [{voice.upper()}] Listening for one command ...")
        action = await assistant.run_once()
        print(f"🤖  {action.response}")
        return

    # Continuous loop
    if mode == "wake":
        print(f"🎙  [{voice.upper()}] Wake-word mode active. Say 'Hey {voice}' to start.")
        await assistant.run_wake_loop()
    else:
        print(f"🎙  [{voice.upper()}] Push-to-talk mode active. Press Enter to speak.")
        await assistant.run_push_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋  Goodbye.")
        sys.exit(0)
