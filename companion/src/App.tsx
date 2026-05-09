import { useState, useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-shell";
import { VoiceOrb } from "./components/VoiceOrb";
import { ChatBubble } from "./components/ChatBubble";
import { StatusBar } from "./components/StatusBar";
import { SettingsPanel } from "./components/SettingsPanel";
import { useCompanion } from "./hooks/useCompanion";
import type { ChatMessage, CompanionMode } from "./types/companion";

function App() {
  const [mode, setMode] = useState<CompanionMode>("idle");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "I'm Daily Jarvis. Hold Space to speak, or click the orb.",
      timestamp: new Date(),
    },
  ]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [persona, setPersona] = useState("jarvis");

  const { connect, disconnect } = useCompanion();

  useEffect(() => {
    // Listen for Tauri events from Rust
    const unlistenMode = listen("mode-changed", (event) => {
      setMode(event.payload as CompanionMode);
    });
    const unlistenWs = listen("ws-connected", () => setWsConnected(true));
    const unlistenWsDisc = listen("ws-disconnected", () => setWsConnected(false));
    const unlistenRecStart = listen("audio-recording-started", () => setIsRecording(true));
    const unlistenRecStop = listen("audio-recording-stopped", () => setIsRecording(false));
    const unlistenTranscription = listen("ws-transcription", (event) => {
      const text = event.payload as string;
      addMessage("user", text);
      setIsProcessing(true);
    });
    const unlistenResponse = listen("ws-response", (event) => {
      const payload = event.payload as { text?: string; action?: string; action_payload?: unknown };
      setIsProcessing(false);
      if (payload.text) {
        addMessage("assistant", payload.text, payload.action);
      }
      if (payload.action === "open_dashboard") {
        handleOpenDashboard();
      }
    });
    const unlistenAudio = listen("ws-audio", (event) => {
      const payload = event.payload as { data?: string; format?: string };
      if (payload.data) {
        playAudio(payload.data, payload.format || "wav");
      }
    });
    const unlistenPersona = listen("persona-changed", (event) => {
      setPersona(event.payload as string);
    });
    const unlistenShowSettings = listen("show-settings", () => {
      setShowSettings(true);
      setMode("active");
    });
    const unlistenWindowShown = listen("window-shown", () => {
      if (mode === "idle") {
        setMode("active");
      }
    });

    // Auto-connect to backend on startup
    connect().catch(console.error);

    return () => {
      unlistenMode.then((f) => f());
      unlistenWs.then((f) => f());
      unlistenWsDisc.then((f) => f());
      unlistenRecStart.then((f) => f());
      unlistenRecStop.then((f) => f());
      unlistenTranscription.then((f) => f());
      unlistenResponse.then((f) => f());
      unlistenAudio.then((f) => f());
      unlistenPersona.then((f) => f());
      unlistenShowSettings.then((f) => f());
      unlistenWindowShown.then((f) => f());
      disconnect();
    };
  }, []);

  // Keyboard: Space to hold-to-talk
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && !e.repeat && !isProcessing && !isSpeaking) {
        e.preventDefault();
        handleStartRecording();
      }
      if (e.code === "Escape") {
        if (showSettings) {
          setShowSettings(false);
        } else if (mode === "active") {
          invoke("set_idle_mode");
          setMode("idle");
        }
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === "Space" && isRecording) {
        e.preventDefault();
        handleStopRecording();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [isRecording, isProcessing, isSpeaking, showSettings, mode]);

  const addMessage = (role: "user" | "assistant", text: string, action?: string) => {
    setMessages((prev) => [
      ...prev,
      { id: `${Date.now()}-${Math.random()}`, role, text, action, timestamp: new Date() },
    ]);
  };

  const handleStartRecording = async () => {
    try {
      await invoke("start_recording");
      setIsRecording(true);
      setMode("active");
    } catch (e) {
      console.error("Failed to start recording:", e);
    }
  };

  const handleStopRecording = async () => {
    try {
      const wavBytes: number[] = await invoke("stop_recording");
      setIsRecording(false);
      setIsProcessing(true);

      // Send audio to backend via WebSocket
      await invoke("send_audio", {
        base64Data: btoa(String.fromCharCode(...wavBytes)),
        sampleRate: 16000,
      });
    } catch (e) {
      console.error("Failed to stop recording:", e);
      setIsRecording(false);
    }
  };

  const handleOrbClick = () => {
    if (isRecording) {
      handleStopRecording();
    } else {
      if (mode === "idle") {
        setMode("active");
        invoke("set_active_mode");
      }
      handleStartRecording();
    }
  };

  const handleSendText = async (text: string) => {
    addMessage("user", text);
    setIsProcessing(true);
    try {
      await invoke("send_text_command", { text });
    } catch (e) {
      console.error("Failed to send text:", e);
      setIsProcessing(false);
    }
  };

  const handleOpenDashboard = async () => {
    try {
      await invoke("get_settings").then((s: unknown) => {
        const set = s as { backend_url: string };
        const url = set.backend_url.replace(/\/$/, "") + "/";
        open(url);
      });
    } catch (e) {
      console.error("Failed to open dashboard:", e);
    }
  };

  const playAudio = (base64Data: string, format: string) => {
    try {
      const byteString = atob(base64Data);
      const ab = new ArrayBuffer(byteString.length);
      const ia = new Uint8Array(ab);
      for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
      }
      const blob = new Blob([ab], { type: format === "mp3" ? "audio/mpeg" : "audio/wav" });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onplay = () => setIsSpeaking(true);
      audio.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(url);
      };
      audio.play();
    } catch (e) {
      console.error("Audio playback error:", e);
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-slate-900/95 text-white select-none">
      {/* Idle Mode: Compact orb bar */}
      {mode === "idle" && (
        <div className="flex items-center justify-between h-full px-4">
          <VoiceOrb
            state={isRecording ? "listening" : isSpeaking ? "speaking" : "idle"}
            onClick={handleOrbClick}
            size={48}
          />
          <StatusBar connected={wsConnected} persona={persona} />
          <button
            onClick={() => {
              setMode("active");
              invoke("set_active_mode");
            }}
            className="p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
          >
            <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      )}

      {/* Active Mode: Full chat + orb */}
      {mode === "active" && (
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
            <div className="flex items-center gap-3">
              <VoiceOrb
                state={isRecording ? "listening" : isProcessing ? "thinking" : isSpeaking ? "speaking" : "idle"}
                onClick={handleOrbClick}
                size={36}
              />
              <div>
                <h1 className="text-sm font-semibold text-white capitalize">{persona}</h1>
                <div className="flex items-center gap-1.5">
                  <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? "bg-emerald-500" : "bg-rose-500"}`} />
                  <span className="text-[10px] text-slate-400">
                    {wsConnected ? "Online" : "Offline"}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
              >
                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
              <button
                onClick={() => {
                  setMode("idle");
                  invoke("set_idle_mode");
                }}
                className="p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
              >
                <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </div>

          {/* Settings Panel */}
          {showSettings && (
            <SettingsPanel
              onClose={() => setShowSettings(false)}
              onPersonaChange={(p) => {
                setPersona(p);
                invoke("set_settings", {
                  settings: { voice_persona: p, backend_url: undefined, shortcut: undefined },
                });
              }}
            />
          )}

          {/* Chat Messages */}
          {!showSettings && (
            <>
              <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
                {messages.map((msg) => (
                  <ChatBubble key={msg.id} message={msg} />
                ))}
                {isProcessing && (
                  <div className="flex gap-2 items-center text-slate-400 text-xs">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    <span className="ml-1">Thinking...</span>
                  </div>
                )}
              </div>

              {/* Input Bar */}
              <div className="px-4 py-3 border-t border-slate-700/50">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    const input = e.currentTarget.elements.namedItem("command") as HTMLInputElement;
                    if (input.value.trim()) {
                      handleSendText(input.value.trim());
                      input.value = "";
                    }
                  }}
                  className="flex items-center gap-2"
                >
                  <input
                    name="command"
                    type="text"
                    placeholder="Type a command..."
                    className="flex-1 px-3 py-2 bg-slate-800/80 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                  />
                  <button
                    type="submit"
                    className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
                  >
                    Send
                  </button>
                </form>
                <p className="mt-1.5 text-[10px] text-center text-slate-500">
                  Hold Space to speak • Esc to minimize • Try: "Fetch news" • "Show trends"
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
