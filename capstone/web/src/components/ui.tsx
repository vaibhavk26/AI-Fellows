import { useEffect, useId, useRef, useState } from "react";
import { animate, motion } from "framer-motion";
import { ChevronDown, Zap } from "lucide-react";

export interface DropdownOption { value: string; label: string }

export function Dropdown({
  value,
  options,
  onChange,
  className = "",
  disabled = false,
  id,
  placeholder = "Select an option",
}: {
  value: string;
  options: DropdownOption[];
  onChange: (value: string) => void;
  className?: string;
  disabled?: boolean;
  id?: string;
  placeholder?: string;
}) {
  const generatedId = useId();
  const controlId = id ?? generatedId;
  const listId = `${controlId}-options`;
  const rootRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const selectedIndex = options.findIndex((option) => option.value === value);
  const [activeIndex, setActiveIndex] = useState(Math.max(selectedIndex, 0));
  const selectedOption = options[selectedIndex];

  useEffect(() => {
    if (!isOpen) return;
    const closeOnOutsideClick = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setIsOpen(false);
    };
    document.addEventListener("pointerdown", closeOnOutsideClick);
    return () => document.removeEventListener("pointerdown", closeOnOutsideClick);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      listRef.current?.querySelector<HTMLElement>(`[data-index="${activeIndex}"]`)?.scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex, isOpen]);

  const openAt = (index: number) => {
    setActiveIndex(Math.max(0, Math.min(index, options.length - 1)));
    setIsOpen(true);
  };

  const choose = (index: number) => {
    const option = options[index];
    setIsOpen(false);
    if (option) onChange(option.value);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      if (!isOpen) openAt(selectedIndex >= 0 ? selectedIndex : 0);
      else setActiveIndex((index) => Math.min(index + 1, options.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      if (!isOpen) openAt(selectedIndex >= 0 ? selectedIndex : options.length - 1);
      else setActiveIndex((index) => Math.max(index - 1, 0));
    } else if (event.key === "Home" && isOpen) {
      event.preventDefault();
      setActiveIndex(0);
    } else if (event.key === "End" && isOpen) {
      event.preventDefault();
      setActiveIndex(options.length - 1);
    } else if ((event.key === "Enter" || event.key === " ") && isOpen) {
      event.preventDefault();
      choose(activeIndex);
    } else if (event.key === "Escape" && isOpen) {
      event.preventDefault();
      setIsOpen(false);
    } else if (event.key === "Tab") {
      setIsOpen(false);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openAt(selectedIndex >= 0 ? selectedIndex : 0);
    }
  };

  return (
    <div ref={rootRef} className="relative w-full">
      <button
        id={controlId}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={listId}
        aria-activedescendant={isOpen && options.length ? `${listId}-${activeIndex}` : undefined}
        disabled={disabled || options.length === 0}
        className={`${className} relative text-left pr-11 disabled:cursor-not-allowed`}
        onClick={() => isOpen ? setIsOpen(false) : openAt(selectedIndex >= 0 ? selectedIndex : 0)}
        onKeyDown={handleKeyDown}
      >
        <span className="block truncate">{selectedOption?.label ?? placeholder}</span>
        <ChevronDown aria-hidden="true" className={`pointer-events-none absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>
      {isOpen && (
        <div
          ref={listRef}
          id={listId}
          role="listbox"
          aria-labelledby={controlId}
          className="absolute left-0 top-full z-50 mt-2 max-h-60 w-full overflow-y-auto rounded-2xl border border-violet-brand/50 bg-ink-900/95 p-1.5 shadow-[0_16px_40px_rgba(5,2,30,0.8)] backdrop-blur-xl"
        >
          {options.map((option, index) => {
            const selected = option.value === value;
            const active = index === activeIndex;
            return (
              <div
                key={option.value}
                id={`${listId}-${index}`}
                data-index={index}
                role="option"
                aria-selected={selected}
                onMouseMove={() => setActiveIndex(index)}
                onPointerDown={(event) => {
                  event.preventDefault();
                  choose(index);
                }}
                className={`cursor-pointer rounded-xl px-3 py-2.5 text-sm transition-colors ${active ? "bg-violet-brand/25 text-white" : "text-white/75 hover:bg-white/10 hover:text-white"} ${selected ? "font-semibold text-white" : ""}`}
              >
                {option.label}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

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
