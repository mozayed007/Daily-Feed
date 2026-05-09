import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Send, Volume2, VolumeX, Monitor, Bot, User, Sparkles } from 'lucide-react';
import { sendVoiceCommand, createVoiceWebSocket } from '../lib/api';
import { VoiceWebSocketMessage } from '../types/api';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  action?: string;
  timestamp: Date;
}

export function VoiceCompanion() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      text: "I'm Daily Jarvis. I can fetch news, detect trends, search the web, and open your dashboard. How can I help?",
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [connected, setConnected] = useState(false);
  const [showDashboardAlert, setShowDashboardAlert] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize WebSocket
  useEffect(() => {
    const ws = createVoiceWebSocket();
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: 'ping' }));
    };

    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const msg: VoiceWebSocketMessage = JSON.parse(event.data);
      handleWsMessage(msg);
    };

    return () => {
      ws.close();
    };
  }, [handleWsMessage]);

  const handleWsMessage = useCallback((msg: VoiceWebSocketMessage) => {
    switch (msg.type) {
      case 'transcription':
        if (msg.text) {
          addMessage('user', msg.text);
        }
        break;
      case 'response':
        setIsProcessing(false);
        setIsListening(false);
        if (msg.text) {
          addMessage('assistant', msg.text, msg.action);
        }
        if (msg.action === 'open_dashboard') {
          setShowDashboardAlert(true);
          setTimeout(() => setShowDashboardAlert(false), 5000);
        }
        break;
      case 'audio':
        if (msg.data && audioEnabled) {
          playAudio(msg.data);
        }
        break;
      case 'error':
        setIsProcessing(false);
        setIsListening(false);
        addMessage('assistant', `Error: ${msg.message || 'Unknown error'}`);
        break;
    }
  }, [audioEnabled]);

  const addMessage = (role: 'user' | 'assistant', text: string, action?: string) => {
    setMessages((prev) => [
      ...prev,
      { id: `${Date.now()}-${Math.random()}`, role, text, action, timestamp: new Date() },
    ]);
  };

  const playAudio = (base64Data: string) => {
    try {
      const byteString = atob(base64Data);
      const ab = new ArrayBuffer(byteString.length);
      const ia = new Uint8Array(ab);
      for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
      }
      const blob = new Blob([ab], { type: 'audio/mpeg' });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onplay = () => setIsSpeaking(true);
      audio.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(url);
      };
      audio.play();
    } catch (e) {
      console.error('Audio playback error:', e);
    }
  };

  // Send text command (fallback when WS is not used or for text input)
  const sendTextCommand = async () => {
    if (!inputText.trim()) return;
    const text = inputText.trim();
    setInputText('');
    addMessage('user', text);
    setIsProcessing(true);

    try {
      const result = await sendVoiceCommand(text);
      setIsProcessing(false);
      addMessage('assistant', result.response || 'No response', result.action);
      if (result.action === 'open_dashboard') {
        setShowDashboardAlert(true);
        setTimeout(() => setShowDashboardAlert(false), 5000);
      }
    } catch (e) {
      setIsProcessing(false);
      addMessage('assistant', 'Sorry, I had trouble processing that.');
    }
  };

  // Push-to-talk microphone recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        // Convert to base64 and send via WebSocket
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = (reader.result as string).split(',')[1];
          wsRef.current?.send(
            JSON.stringify({
              type: 'audio',
              data: base64,
              sample_rate: 16000,
            })
          );
        };
        reader.readAsDataURL(audioBlob);
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorder.start();
      setIsListening(true);
      setIsProcessing(true);
    } catch (e) {
      console.error('Microphone error:', e);
      addMessage('assistant', 'I cannot access your microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsListening(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendTextCommand();
    }
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="relative">
            <motion.div
              animate={
                isSpeaking
                  ? { scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }
                  : isProcessing
                  ? { scale: [1, 1.1, 1], opacity: [0.7, 1, 0.7] }
                  : { scale: 1, opacity: 0.6 }
              }
              transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute inset-0 bg-blue-500 rounded-full blur-xl"
            />
            <div className="relative w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
              <Bot className="w-6 h-6 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">Daily Jarvis</h1>
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <span
                className={`w-2 h-2 rounded-full ${
                  connected ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
              />
              {connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAudioEnabled(!audioEnabled)}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title={audioEnabled ? 'Mute voice' : 'Unmute voice'}
          >
            {audioEnabled ? (
              <Volume2 className="w-5 h-5 text-slate-600 dark:text-slate-300" />
            ) : (
              <VolumeX className="w-5 h-5 text-slate-400" />
            )}
          </button>
        </div>
      </div>

      {/* Dashboard Alert */}
      <AnimatePresence>
        {showDashboardAlert && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-xl flex items-center gap-3"
          >
            <Monitor className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <span className="text-sm text-blue-800 dark:text-blue-200">
              Opening the dashboard for you...
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-[300px] max-h-[60vh] pr-2">
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.role === 'assistant'
                  ? 'bg-gradient-to-br from-blue-500 to-purple-600'
                  : 'bg-slate-200 dark:bg-slate-700'
              }`}
            >
              {msg.role === 'assistant' ? (
                <Sparkles className="w-4 h-4 text-white" />
              ) : (
                <User className="w-4 h-4 text-slate-600 dark:text-slate-300" />
              )}
            </div>
            <div
              className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm ${
                msg.role === 'assistant'
                  ? 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 shadow-sm'
                  : 'bg-blue-600 text-white'
              }`}
            >
              <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
              {msg.action && msg.action !== 'none' && (
                <span className="inline-block mt-2 px-2 py-0.5 text-[10px] rounded-full bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400">
                  action: {msg.action}
                </span>
              )}
            </div>
          </motion.div>
        ))}
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white animate-pulse" />
            </div>
            <div className="px-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
        <div className="flex items-end gap-2">
          {/* Push-to-talk button */}
          <button
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
            className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center transition-all duration-200 ${
              isListening
                ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/30 scale-110'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
            title="Hold to speak"
          >
            {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          {/* Text input */}
          <div className="flex-1 relative">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Jarvis anything... (e.g., 'Fetch news', 'Show trends', 'Search AI breakthroughs')"
              rows={1}
              className="w-full px-4 py-3 bg-slate-100 dark:bg-slate-800 border-0 rounded-xl text-sm text-slate-800 dark:text-slate-200 placeholder:text-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 max-h-32"
              style={{ minHeight: '48px' }}
            />
          </div>

          {/* Send button */}
          <button
            onClick={sendTextCommand}
            disabled={!inputText.trim() || isProcessing}
            className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center transition-all ${
              inputText.trim() && !isProcessing
                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-500/20'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        <p className="mt-2 text-xs text-center text-slate-400 dark:text-slate-500">
          Hold the mic button to speak, or type your command. Try: “Fetch news”, “What are the trends?”,
          “Search for quantum computing news”, “Open dashboard”
        </p>
      </div>
    </div>
  );
}
