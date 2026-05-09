import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { CompanionSettings } from "../types/companion";

interface SettingsPanelProps {
  onClose: () => void;
  onPersonaChange: (persona: string) => void;
}

export function SettingsPanel({ onClose, onPersonaChange }: SettingsPanelProps) {
  const [settings, setSettings] = useState<CompanionSettings>({
    backend_url: "http://localhost:8000",
    voice_persona: "jarvis",
    shortcut: "Ctrl+Shift+Space",
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    invoke<CompanionSettings>("get_settings").then((s) => {
      setSettings(s);
    }).catch(console.error);
  }, []);

  const handleSave = async () => {
    try {
      await invoke("set_settings", { settings });
      onPersonaChange(settings.voice_persona);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      console.error("Failed to save settings:", e);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Settings</h2>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-700/50 transition-colors">
          <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="space-y-1.5">
        <label className="text-xs text-slate-400">Backend URL</label>
        <input
          type="text"
          value={settings.backend_url}
          onChange={(e) => setSettings({ ...settings, backend_url: e.target.value })}
          className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700/50 rounded-lg text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500/50"
        />
      </div>

      <div className="space-y-1.5">
        <label className="text-xs text-slate-400">Voice Persona</label>
        <div className="flex gap-2">
          {["jarvis", "friday"].map((p) => (
            <button
              key={p}
              onClick={() => setSettings({ ...settings, voice_persona: p })}
              className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium capitalize transition-colors ${
                settings.voice_persona === p
                  ? "bg-blue-600 text-white"
                  : "bg-slate-800/80 text-slate-400 hover:bg-slate-700/50"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="text-xs text-slate-400">Global Shortcut</label>
        <input
          type="text"
          value={settings.shortcut}
          onChange={(e) => setSettings({ ...settings, shortcut: e.target.value })}
          className="w-full px-3 py-2 bg-slate-800/80 border border-slate-700/50 rounded-lg text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500/50"
          placeholder="Ctrl+Shift+Space"
        />
        <p className="text-[10px] text-slate-500">Press this key combo to show/hide the companion</p>
      </div>

      <button
        onClick={handleSave}
        className={`w-full py-2 rounded-lg text-xs font-medium text-white transition-colors ${
          saved ? "bg-emerald-600" : "bg-blue-600 hover:bg-blue-700"
        }`}
      >
        {saved ? "Saved!" : "Save Settings"}
      </button>

      <div className="pt-2 border-t border-slate-700/50 space-y-1">
        <p className="text-[10px] text-slate-500">Daily Jarvis Companion v0.1.0</p>
        <p className="text-[10px] text-slate-600">Distil-Whisper STT • Kokoro TTS • Local AI</p>
      </div>
    </div>
  );
}
