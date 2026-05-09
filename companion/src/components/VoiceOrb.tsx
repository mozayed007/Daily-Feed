import { motion } from "framer-motion";
import type { VoiceState } from "../types/companion";

interface VoiceOrbProps {
  state: VoiceState;
  onClick?: () => void;
  size?: number;
}

export function VoiceOrb({ state, onClick, size = 48 }: VoiceOrbProps) {
  const isListening = state === "listening";
  const isThinking = state === "thinking";
  const isSpeaking = state === "speaking";
  const isActive = isListening || isThinking || isSpeaking;

  return (
    <button
      onClick={onClick}
      className="relative flex items-center justify-center rounded-full"
      style={{ width: size, height: size }}
    >
      {/* Background pulse rings */}
      {isListening && (
        <>
          <motion.div
            className="absolute inset-0 rounded-full bg-blue-500/30"
            animate={{ scale: [1, 1.6, 1], opacity: [0.5, 0, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute inset-0 rounded-full bg-blue-500/20"
            animate={{ scale: [1, 2, 1], opacity: [0.3, 0, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
          />
        </>
      )}

      {isThinking && (
        <motion.div
          className="absolute inset-0 rounded-full bg-amber-500/20"
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          style={{
            background: "conic-gradient(from 0deg, transparent, rgba(245,158,11,0.3), transparent)",
          }}
        />
      )}

      {isSpeaking && (
        <motion.div
          className="absolute inset-0 rounded-full bg-emerald-500/20"
          animate={{ scale: [1, 1.15, 1], opacity: [0.4, 0.7, 0.4] }}
          transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut" }}
        />
      )}

      {/* Core orb */}
      <motion.div
        className="relative rounded-full flex items-center justify-center"
        style={{
          width: size * 0.7,
          height: size * 0.7,
          background: isActive
            ? isListening
              ? "linear-gradient(135deg, #3b82f6, #2563eb)"
              : isThinking
              ? "linear-gradient(135deg, #f59e0b, #d97706)"
              : "linear-gradient(135deg, #10b981, #059669)"
            : "linear-gradient(135deg, #475569, #334155)",
          boxShadow: isActive
            ? `0 0 ${size * 0.3}px ${isListening ? "rgba(59,130,246,0.5)" : isThinking ? "rgba(245,158,11,0.5)" : "rgba(16,185,129,0.5)"}`
            : "none",
        }}
        animate={
          isListening
            ? { scale: [1, 1.05, 1] }
            : isThinking
            ? { scale: [1, 0.95, 1] }
            : { scale: 1 }
        }
        transition={{ duration: 0.6, repeat: isListening || isThinking ? Infinity : 0, ease: "easeInOut" }}
      >
        {/* Mic icon or waveform bars */}
        {isSpeaking ? (
          <div className="flex items-end gap-[2px] h-3">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-[3px] bg-white rounded-full"
                animate={{ height: [4, 12, 6, 14, 4] }}
                transition={{
                  duration: 0.5 + i * 0.1,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />
            ))}
          </div>
        ) : (
          <svg className="text-white" width={size * 0.3} height={size * 0.3} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            {isListening ? (
              <>
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" x2="12" y1="19" y2="22" />
              </>
            ) : (
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            )}
          </svg>
        )}
      </motion.div>
    </button>
  );
}
