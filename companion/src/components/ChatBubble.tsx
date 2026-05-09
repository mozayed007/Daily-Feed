import type { ChatMessage } from "../types/companion";

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-2 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className={`w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] font-bold ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-slate-700 text-slate-300"
        }`}
      >
        {isUser ? "U" : "J"}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[80%] px-3 py-2 rounded-xl text-xs leading-relaxed ${
          isUser
            ? "bg-blue-600/90 text-white"
            : "bg-slate-800/80 border border-slate-700/50 text-slate-200"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.text}</p>
        {message.action && message.action !== "none" && (
          <span className="inline-block mt-1 px-1.5 py-0.5 text-[9px] rounded bg-slate-700/60 text-slate-400">
            {message.action}
          </span>
        )}
      </div>
    </div>
  );
}
