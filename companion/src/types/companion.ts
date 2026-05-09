export type CompanionMode = "idle" | "active";
export type VoiceState = "idle" | "listening" | "thinking" | "speaking";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  action?: string;
  timestamp: Date;
}

export interface CompanionSettings {
  backend_url: string;
  voice_persona: string;
  shortcut: string;
}
