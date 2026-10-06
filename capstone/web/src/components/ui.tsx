import { useEffect, useRef, useState } from "react";
import { animate, motion } from "framer-motion";
import { Zap } from "lucide-react";

export function Aurora() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-ink-950">
      <div className="animate-float absolute -left-32 -top-32 h-[34rem] w-[34rem] rounded-full bg-violet-brand/30 blur-[120px]" />
      <div className="animate-float absolute -right-24 top-1/4 h-[30rem] w-[30rem] rounded-full bg-pink-brand/20 blur-[120px]" style={{ animationDelay: "-3s" }} />
      <div className="animate-float absolute bottom-[-10rem] left-1/3 h-[28rem] w-[28rem] rounded-full bg-cyan-brand/15 blur-[120px]" style={{ animationDelay: "-5s" }} />
      <div
        className="absolute inset-0 opacity-[0.07]"
        style={{ backgroundImage: "radial-gradient(#fff 1px, transparent 1px)", backgroundSize: "28px 28px" }}
      />
    </div>
  );
}

export function Logo({ size = "md" }: { size?: "md" | "lg" }) {
  const big = size === "lg";
  return (
    <div className="flex items-center gap-2.5">
      <div className={`btn-primary grid place-items-center rounded-2xl ${big ? "h-12 w-12" : "h-9 w-9"}`}>
        <Zap className={big ? "h-6 w-6" : "h-5 w-5"} fill="white" />
      </div>
      <span className={`font-display font-bold tracking-tight ${big ? "text-3xl" : "text-xl"}`}>
        Exam<span className="text-gradient">IQ</span>
      </span>
    </div>
  );
}

export function CountUp({ value, decimals = 0, suffix = "" }: { value: number; decimals?: number; suffix?: string }) {
  const [display, setDisplay] = useState(0);
  const prev = useRef(0);
  useEffect(() => {
    const controls = animate(prev.current, value, {
      duration: 1.1,
      ease: "easeOut",
      onUpdate: (v) => setDisplay(v),
    });
    prev.current = value;
    return () => controls.stop();
  }, [value]);
  return <>{display.toFixed(decimals)}{suffix}</>;
}

export function ProgressRing({ value, size = 150, stroke = 14, children }: { value: number; size?: number; stroke?: number; children?: React.ReactNode }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#7c5cff" />
            <stop offset="55%" stopColor="#ff4fa3" />
            <stop offset="100%" stopColor="#ffc247" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(255,255,255,0.08)" strokeWidth={stroke} fill="none" />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r} stroke="url(#ring)" strokeWidth={stroke} fill="none" strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - clamped / 100) }}
          transition={{ duration: 1.3, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">{children}</div>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-2xl bg-white/[0.06] ${className}`} />;
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-2xl border border-pink-brand/40 bg-pink-brand/10 px-4 py-3 text-sm text-pink-100">
      {message}
    </div>
  );
}
