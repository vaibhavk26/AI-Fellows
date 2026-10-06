import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Link, useSearchParams } from "react-router-dom";
import confetti from "canvas-confetti";
import { Check, Clock, Rocket, Target, X } from "lucide-react";
import { CountUp, ErrorNote, ProgressRing, Skeleton } from "../components/ui";
import { api } from "../lib/api";
import { BAND_COLOR, BAND_LABEL, band, computeXp } from "../lib/gamify";
import { formatDuration, parseTimestamp } from "../lib/time";
import type { AnswerResult, AttemptResult } from "../lib/types";

const num = (v: number | string | null | undefined) => Number(v ?? 0) || 0;

function Review({ a, index }: { a: AnswerResult; index: number }) {
  const mcq = a.question_type === "mcq" && a.options;
  return (
    <motion.article initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className={`glass rounded-3xl border-l-4 p-5 sm:p-6 ${a.is_correct ? "border-l-lime-brand" : "border-l-pink-brand"}`}>
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-display text-lg font-bold">Q{index + 1}. {a.question_text}</h3>
        <span className={`flex shrink-0 items-center gap-1 rounded-full px-3 py-1 text-xs font-bold ${a.is_correct ? "bg-lime-brand/15 text-lime-brand" : "bg-pink-brand/15 text-pink-300"}`}>
          {a.is_correct ? <Check className="h-3.5 w-3.5" /> : <X className="h-3.5 w-3.5" />}{Number(a.score_awarded)}/{Number(a.max_score)}
        </span>
      </div>
      {a.topic_name && <p className="mt-1 text-xs text-white/40">{a.topic_name}</p>}
      <div className="mt-4 space-y-2">
        {mcq ? a.options!.map((o) => {
          const isCorrect = o.key === a.correct_answer;
          const isMine = o.key === a.submitted_answer;
          const cls = isCorrect ? "border-lime-brand/60 bg-lime-brand/10" : isMine ? "border-pink-brand/60 bg-pink-brand/10" : "border-white/10 bg-white/[0.03]";
          return (
            <div key={o.key} className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm ${cls}`}>
              <span className="font-bold">{o.key}.</span><span className="flex-1">{o.text}</span>
              {isCorrect && isMine && <span className="text-xs font-semibold text-lime-brand">Your answer · correct</span>}
              {isCorrect && !isMine && <span className="text-xs font-semibold text-lime-brand">Correct answer</span>}
              {isMine && !isCorrect && <span className="text-xs font-semibold text-pink-300">Your answer</span>}
            </div>
          );
        }) : (
          <div className="grid gap-2 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm"><p className="text-xs text-white/40">Your answer</p>{a.submitted_answer || "No answer"}</div>
            <div className="rounded-2xl border border-lime-brand/50 bg-lime-brand/10 px-4 py-3 text-sm"><p className="text-xs text-white/40">Correct answer</p>{a.correct_answer}</div>
          </div>
        )}
        {mcq && !a.submitted_answer && <p className="text-xs text-white/40">You did not answer this question.</p>}
      </div>
      <p className="mt-4 rounded-2xl bg-white/5 px-4 py-3 text-sm text-white/70"><span className="font-semibold text-cyan-brand">Explanation · </span>{a.explanation || "No explanation is available for this question."}</p>
    </motion.article>
  );
}

function Metric({ icon, label, children }: { icon: React.ReactNode; label: string; children: React.ReactNode }) {
  return (
    <div className="glass rounded-3xl p-5">
      <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-white/50">{icon}{label}</p>
      <p className="mt-2 font-display text-3xl font-bold">{children}</p>
    </div>
  );
}

export default function ResultsPage() {
  const [params, setParams] = useSearchParams();
  const attempts = useQuery({ queryKey: ["attempts"], queryFn: api.attempts });
  const list = attempts.data ?? [];
  const selectedId = params.get("attempt") ?? list[0]?.id ?? "";
  const isNew = params.get("new") === "1";

  const detail = useQuery({ queryKey: ["attempt", selectedId], queryFn: () => api.attemptDetail(selectedId), enabled: !!selectedId });
  const summary = list.find((a) => a.id === selectedId);
  const r: AttemptResult | undefined = detail.data;

  const [onlyMistakes, setOnlyMistakes] = useState(false);
  const selectedIdx = list.findIndex((a) => a.id === selectedId);
  const prev = selectedIdx >= 0 ? list[selectedIdx + 1] : undefined;

  const percentage = r ? num(r.percentage) : 0;
  const correct = r ? r.answers.filter((a) => a.is_correct).length : 0;
  const total = r?.answers.length ?? 0;

  useEffect(() => {
    if (!r || !isNew || percentage < 70 || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const end = Date.now() + 1200;
    const frame = () => {
      confetti({ particleCount: 5, angle: 60, spread: 70, origin: { x: 0 }, colors: ["#7c5cff", "#ff4fa3", "#22d3ee", "#a3ff6b", "#ffc247"] });
      confetti({ particleCount: 5, angle: 120, spread: 70, origin: { x: 1 }, colors: ["#7c5cff", "#ff4fa3", "#22d3ee", "#a3ff6b", "#ffc247"] });
      if (Date.now() < end) requestAnimationFrame(frame);
    };
    frame();
  }, [r?.id, isNew, percentage]);

  const topics = useMemo(() => {
    const map = new Map<string, { c: number; t: number }>();
    r?.answers.forEach((a) => {
      const k = a.topic_name || "Unknown topic";
      const v = map.get(k) ?? { c: 0, t: 0 };
      v.t += 1; if (a.is_correct) v.c += 1;
      map.set(k, v);
    });
    return [...map.entries()];
  }, [r]);

  if (attempts.isLoading) return <Skeleton className="h-96" />;
  if (attempts.isError) return <ErrorNote message={(attempts.error as Error).message} />;
  if (list.length === 0) {
    return (
      <div className="glass mx-auto mt-10 max-w-lg rounded-3xl p-10 text-center">
        <div className="text-5xl">🏆</div>
        <h1 className="mt-4 font-display text-2xl font-bold">No results yet</h1>
        <p className="mt-2 text-white/55">Submit an exam to see your score, explanations and weak spots here.</p>
        <Link to="/exam" className="btn-primary mt-6 inline-flex items-center gap-2 rounded-2xl px-6 py-3 font-bold"><Rocket className="h-4 w-4" />Take an exam</Link>
      </div>
    );
  }

  const b = band(percentage);
  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">{isNew ? "Exam submitted 🎉" : "Your results"}</p>
          <h1 className="font-display text-4xl font-bold">Quest <span className="text-gradient">report</span></h1>
        </div>
        <label className="text-xs font-semibold uppercase tracking-wider text-white/50">Attempt
          <select value={selectedId} onChange={(e) => setParams({ attempt: e.target.value })} className="mt-1 block w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm normal-case tracking-normal text-white outline-none focus:border-violet-brand">
            {list.map((a, i) => (
              <option key={a.id} value={a.id} className="bg-ink-900">
                Attempt {list.length - i} · {a.submitted_at ? parseTimestamp(a.submitted_at).toLocaleString() : "—"} · {num(a.percentage).toFixed(1)}%
              </option>
            ))}
          </select>
        </label>
      </header>

      {detail.isLoading && <Skeleton className="h-64" />}
      {detail.isError && <ErrorNote message={(detail.error as Error).message} />}
      {r && (
        <>
          <section className="glass relative overflow-hidden rounded-3xl p-6 sm:p-8">
            <div className="flex flex-col items-center gap-8 md:flex-row">
              <ProgressRing value={percentage} size={180}>
                <span className="font-display text-4xl font-bold"><CountUp value={percentage} decimals={0} />%</span>
              </ProgressRing>
              <div className="text-center md:text-left">
                <p className="font-display text-3xl font-bold" style={{ color: BAND_COLOR[b] }}>{BAND_LABEL[b]}</p>
                <p className="mt-1 text-white/60">You scored {Number(r.score)} out of {Number(r.max_score)} marks.</p>
                <Link to="/exam" className="btn-primary mt-4 inline-flex items-center gap-2 rounded-2xl px-5 py-2.5 text-sm font-bold"><Rocket className="h-4 w-4" />Play again</Link>
              </div>
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric icon={<Target className="h-4 w-4" />} label="Score">{Number(r.score)}/{Number(r.max_score)}</Metric>
            <Metric icon={<Target className="h-4 w-4" />} label="Percentage">{percentage.toFixed(1)}%</Metric>
            <Metric icon={<Check className="h-4 w-4" />} label="Accuracy">{correct}/{total}</Metric>
            <Metric icon={<Clock className="h-4 w-4" />} label="Time taken">{formatDuration(summary?.started_at, summary?.submitted_at ?? r.submitted_at)}</Metric>
          </section>

          <section className="glass rounded-3xl p-6">
            <h2 className="mb-3 font-display text-xl font-bold">Coach says</h2>
            <ul className="space-y-2 text-sm text-white/75">
              <li>⚡ You earned <strong className="text-amber-brand">+{computeXp(total, percentage)} XP</strong> for this quest.</li>
              {prev ? (() => {
                const d = percentage - num(prev.percentage);
                return <li>{d > 0 ? "📈" : d < 0 ? "📉" : "➖"} {d === 0 ? "Same score as your previous attempt." : `${Math.abs(d).toFixed(0)} points ${d > 0 ? "higher" : "lower"} than your previous attempt${d > 0 ? " ? keep climbing!" : " ? shake it off and go again."}`}</li>;
              })() : <li>🌟 This is your first recorded attempt. Every great streak starts here.</li>}
              {(() => {
                const weak = topics.filter(([n, v]) => v.c < v.t && n !== "Unknown topic").sort((a, b2) => a[1].c / a[1].t - b2[1].c / b2[1].t)[0];
                return weak ? <li>🎯 Focus next on <strong>{weak[0]}</strong> ({weak[1].c}/{weak[1].t} correct). <Link to="/exam" className="font-semibold text-cyan-brand hover:underline">Practise it</Link></li> : <li>?? Every question correct. Try a harder exam!</li>;
              })()}
            </ul>
          </section>

          {topics.length > 0 && (
            <section className="glass rounded-3xl p-6">
              <h2 className="mb-4 font-display text-xl font-bold">Topic breakdown</h2>
              <div className="space-y-3">
                {topics.map(([name, v]) => (
                  <div key={name}>
                    <div className="mb-1 flex justify-between text-sm"><span>{name}</span><span className="text-white/60">{v.c}/{v.t} correct</span></div>
                    <div className="h-2.5 overflow-hidden rounded-full bg-white/10"><motion.div initial={{ width: 0 }} animate={{ width: `${(v.c / v.t) * 100}%` }} transition={{ duration: 0.8 }} className="h-full rounded-full" style={{ background: BAND_COLOR[band((v.c / v.t) * 100)] }} /></div>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-display text-2xl font-bold">Question review</h2>
              {correct < total && (
                <button type="button" aria-pressed={onlyMistakes} onClick={() => setOnlyMistakes((v) => !v)} className={`rounded-full border px-4 py-2 text-sm font-semibold ${onlyMistakes ? "border-pink-brand bg-pink-brand/15 text-pink-300" : "border-white/15 text-white/70 hover:bg-white/5"}`}>
                  {onlyMistakes ? "Showing mistakes only" : "Show mistakes only"}
                </button>
              )}
            </div>
            {r.answers.map((a, i) => (onlyMistakes && a.is_correct ? null : <Review key={a.question_id} a={a} index={i} />))}
          </section>
        </>
      )}
    </div>
  );
}
