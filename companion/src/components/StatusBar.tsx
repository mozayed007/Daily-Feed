interface StatusBarProps {
  connected: boolean;
  persona: string;
}

export function StatusBar({ connected, persona }: StatusBarProps) {
  return (
    <div className="flex items-center gap-2">
      <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-emerald-500" : "bg-rose-500"}`} />
      <span className="text-[10px] text-slate-400 capitalize">{persona}</span>
    </div>
  );
}
