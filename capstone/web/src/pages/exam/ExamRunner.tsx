import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Flag, Loader2, Send, Timer, X } from "lucide-react";
import { ErrorNote } from "../../components/ui";
import { api } from "../../lib/api";
import { formatClock, remainingSeconds } from "../../lib/time";
import type { AttemptResult } from "../../lib/types";
import type { ActiveExam } from "./ExamSetup";

interface Props {
  active: ActiveExam;
  answers: Record<string, string>;
  index: number;
  onAnswers: (a: Record<string, string>) => void;
  onIndex: (i: number) => void;
  onSubmitted: (result: AttemptResult) => void;
  onEnd: () => void;
}

function Modal({ children, onClose, label }: { children: React.ReactNode; onClose: () => void; label: string }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 grid place-items-center bg-ink-950/80 p-4 backdrop-blur-sm" onClick={onClose}>
      <motion.div role="dialog" aria-modal="true" aria-label={label} initial={{ scale: 0.92, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95 }} onClick={(e) => e.stopPropagation()} className="glass w-full max-w-md rounded-3xl bg-ink-900/90 p-7">
        {children}
      </motion.div>
    </motion.div>
  );
}

export default function ExamRunner({ active, answers, index, onAnswers, onIndex, onSubmitted, onEnd }: Props) {
  const { exam, attempt } = active;
  const qc = useQueryClient();
  const questions = exam.questions;
  const [now, setNow] = useState(() => Date.now());
  const [dialog, setDialog] = useState<null | "submit" | "end">(null);
  const [flagged, setFlagged] = useState<Set<string>>(new Set());

  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const left = remainingSeconds(attempt.started_at, exam.time_limit_minutes, now);
  const total = exam.time_limit_minutes * 60;
  const urgent = left <= 60;

  const submit = useMutation({
    mutationFn: () => {
      const payload = questions
        .map((q) => ({ question_id: q.question.id, answer: (answers[q.question.id] ?? "").trim() }))
        .filter((a) => a.answer);
      return api.submitAttempt(attempt.id, payload);
    },
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["analytics"] });
      qc.invalidateQueries({ queryKey: ["assignments"] });
      qc.invalidateQueries({ queryKey: ["attempts"] });
      qc.setQueryData(["attempt", result.id], result);
      onSubmitted(result);
    },
  });

  if (questions.length === 0) {
    return <div className="glass rounded-3xl p-8 text-center text-white/60">This exam has no questions. <button className="underline" onClick={onEnd}>Back</button></div>;
  }

  const current = questions[Math.min(index, questions.length - 1)];
  const q = current.question;
  const value = answers[q.id] ?? "";
  const answered = questions.filter((x) => (answers[x.question.id] ?? "").trim()).length;
  const setAnswer = (v: string) => onAnswers(v.trim() ? { ...answers, [q.id]: v } : Object.fromEntries(Object.entries(answers).filter(([k]) => k !== q.id)));
  const go = (i: number) => onIndex(Math.max(0, Math.min(questions.length - 1, i)));
  const unanswered = questions.length - answered;

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="min-w-0">
          <h1 className="truncate font-display text-3xl font-bold">{exam.title}</h1>
          <p className="text-sm text-white/50">{questions.length} questions · {exam.time_limit_minutes} minutes · {answered} answered</p>
        </div>
        <div className="flex items-center gap-3">
          <div role="timer" aria-label="Time remaining" className={`flex items-center gap-2 rounded-2xl px-4 py-2.5 font-display text-2xl font-bold tabular-nums ${urgent ? "animate-pulse-glow bg-pink-brand/20 text-pink-300" : "glass"}`}>
            <Timer className="h-5 w-5" />{formatClock(left)}
          </div>
          <button onClick={() => setDialog("end")} className="rounded-2xl border border-pink-brand/40 px-4 py-3 text-sm font-semibold text-pink-300 transition hover:bg-pink-brand/10">End exam</button>
        </div>
      </header>

      <div className="h-1.5 overflow-hidden rounded-full bg-white/10" aria-hidden>
        <motion.div className="h-full rounded-full bg-gradient-to-r from-cyan-brand to-violet-brand" animate={{ width: `${(left / total) * 100}%` }} transition={{ ease: "linear", duration: 1 }} />
      </div>
      {left === 0 && <ErrorNote message="Time is up. Submit your answers to complete this attempt." />}

      <div className="grid gap-5 lg:grid-cols-[1fr_16rem]">
        <AnimatePresence mode="wait">
          <motion.section key={q.id} initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.2 }} className="glass rounded-3xl p-6 sm:p-8">
            <div className="mb-4 flex items-center justify-between text-xs font-semibold uppercase tracking-wider">
              <span className="text-cyan-brand">Question {Math.min(index, questions.length - 1) + 1} of {questions.length}</span>
              <span className="flex items-center gap-2 text-white/50">
                <span className="rounded-full bg-white/10 px-3 py-1">{q.marks} {q.marks === 1 ? "mark" : "marks"}</span>
                <span className="rounded-full bg-white/10 px-3 py-1">{q.question_type === "mcq" ? "MCQ" : "Numerical"}</span>
              </span>
            </div>
            <h2 className="font-display text-2xl font-bold leading-snug">{q.question_text}</h2>

            <div className="mt-6 space-y-3" role={q.question_type === "mcq" ? "radiogroup" : undefined} aria-label="Answer options">
              {q.question_type === "mcq" ? (q.options ?? []).map((opt) => {
                const selected = value === opt.key;
                return (
                  <motion.button key={opt.key} role="radio" aria-checked={selected} whileHover={{ x: 4 }} whileTap={{ scale: 0.99 }} onClick={() => setAnswer(opt.key)}
                    className={`flex w-full items-center gap-4 rounded-2xl border p-4 text-left transition ${selected ? "border-violet-brand bg-violet-brand/20 shadow-[0_0_24px_-6px_rgba(124,92,255,0.8)]" : "border-white/10 bg-white/[0.04] hover:border-white/25"}`}>
                    <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl text-sm font-bold ${selected ? "btn-primary" : "bg-white/10"}`}>{opt.key}</span>
                    <span>{opt.text}</span>
                  </motion.button>
                );
              }) : (
                <div>
                  <label htmlFor="answer" className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-white/50">Your answer</label>
                  <input id="answer" value={value} onChange={(e) => setAnswer(e.target.value)} placeholder="Enter your answer" autoComplete="off" className="w-full rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-lg outline-none focus:border-violet-brand focus:ring-4 focus:ring-violet-brand/20" />
                </div>
              )}
            </div>

            <div className="mt-8 flex items-center justify-between gap-3">
              <button onClick={() => go(index - 1)} disabled={index === 0} className="flex items-center gap-1 rounded-2xl bg-white/10 px-5 py-3 text-sm font-semibold transition hover:bg-white/15 disabled:opacity-30"><ChevronLeft className="h-4 w-4" />Previous</button>
              <button onClick={() => setFlagged((s) => { const n = new Set(s); n.has(q.id) ? n.delete(q.id) : n.add(q.id); return n; })} aria-pressed={flagged.has(q.id)} className={`flex items-center gap-1.5 rounded-2xl px-4 py-3 text-sm font-semibold transition ${flagged.has(q.id) ? "bg-amber-brand/20 text-amber-brand" : "text-white/50 hover:text-white"}`}><Flag className="h-4 w-4" />{flagged.has(q.id) ? "Flagged" : "Flag"}</button>
              {index < questions.length - 1 ? (
                <button onClick={() => go(index + 1)} className="btn-primary flex items-center gap-1 rounded-2xl px-6 py-3 text-sm font-bold">Next<ChevronRight className="h-4 w-4" /></button>
              ) : (
                <button onClick={() => setDialog("submit")} className="btn-primary flex items-center gap-2 rounded-2xl px-6 py-3 text-sm font-bold"><Send className="h-4 w-4" />Submit</button>
              )}
            </div>
          </motion.section>
        </AnimatePresence>

        <aside className="glass h-fit rounded-3xl p-5">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-white/50">Question map</p>
          <div className="grid grid-cols-5 gap-2">
            {questions.map((x, i) => {
              const isAnswered = !!(answers[x.question.id] ?? "").trim();
              const isCurrent = i === index;
              return (
                <button key={x.id} onClick={() => go(i)} aria-label={`Go to question ${i + 1}${isAnswered ? ", answered" : ""}${flagged.has(x.question.id) ? ", flagged" : ""}`} aria-current={isCurrent ? "true" : undefined}
                  className={`relative aspect-square rounded-xl text-sm font-bold transition ${isCurrent ? "btn-primary" : isAnswered ? "bg-lime-brand/25 text-lime-brand" : "bg-white/10 text-white/60 hover:bg-white/20"}`}>
                  {i + 1}
                  {flagged.has(x.question.id) && <span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-amber-brand" />}
                </button>
              );
            })}
          </div>
          <div className="mt-5">
            <div className="mb-1 flex justify-between text-xs text-white/50"><span>Answered</span><span>{answered}/{questions.length}</span></div>
            <div className="h-2 overflow-hidden rounded-full bg-white/10"><motion.div className="h-full rounded-full bg-lime-brand" animate={{ width: `${(answered / questions.length) * 100}%` }} /></div>
          </div>
          <button onClick={() => setDialog("submit")} className="btn-primary mt-5 flex w-full items-center justify-center gap-2 rounded-2xl py-3 text-sm font-bold"><Send className="h-4 w-4" />Submit exam</button>
        </aside>
      </div>

      <AnimatePresence>
        {dialog === "submit" && (
          <Modal label="Submit this exam?" onClose={() => !submit.isPending && setDialog(null)}>
            <h2 className="font-display text-2xl font-bold">Submit this exam?</h2>
            <p className="mt-3 text-white/70">You have answered <strong>{answered} of {questions.length} questions</strong>.</p>
            {unanswered > 0 && <p className="mt-2 rounded-2xl bg-amber-brand/15 px-4 py-3 text-sm text-amber-200">{unanswered} unanswered question(s) will receive zero marks.</p>}
            <p className="mt-2 text-sm text-white/50">After submission, your answers cannot be changed.</p>
            {submit.isError && <div className="mt-4"><ErrorNote message={(submit.error as Error).message} /></div>}
            <div className="mt-6 grid grid-cols-2 gap-3">
              <button disabled={submit.isPending} onClick={() => submit.mutate()} className="btn-primary flex items-center justify-center gap-2 rounded-2xl py-3 font-bold">{submit.isPending && <Loader2 className="h-4 w-4 animate-spin" />}Submit exam</button>
              <button disabled={submit.isPending} onClick={() => setDialog(null)} className="rounded-2xl bg-white/10 py-3 font-semibold hover:bg-white/15">Keep working</button>
            </div>
          </Modal>
        )}
        {dialog === "end" && (
          <Modal label="End exam?" onClose={() => setDialog(null)}>
            <div className="flex items-start justify-between"><h2 className="font-display text-2xl font-bold">End exam?</h2><button aria-label="Close" onClick={() => setDialog(null)}><X className="h-5 w-5 text-white/50" /></button></div>
            <p className="mt-3 text-white/70">Are you sure you want to end this examination? Your exam will end, and your responses will not be saved.</p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              <button onClick={() => setDialog(null)} className="btn-primary rounded-2xl py-3 font-bold">Continue exam</button>
              <button onClick={onEnd} className="rounded-2xl border border-pink-brand/50 py-3 font-semibold text-pink-300 hover:bg-pink-brand/10">End exam</button>
            </div>
          </Modal>
        )}
      </AnimatePresence>
    </div>
  );
}
