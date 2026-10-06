import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChevronDown, Flame, ListChecks, Percent, TrendingUp } from "lucide-react";
import { CountUp, ErrorNote, Skeleton } from "../components/ui";
import { api } from "../lib/api";
import { BAND_COLOR, BAND_LABEL, band, pct } from "../lib/gamify";
import type { AttemptDetail, ScoreRow } from "../lib/types";

const PERIODS = [
  { label: "All time", days: null },
  { label: "Last 30 days", days: 30 },
  { label: "Last 90 days", days: 90 },
  { label: "This year", days: "year" as const },
];

const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const selectCls = "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm outline-none focus:border-violet-brand";

function Bar({ label, score, sub }: { label: string; score: number; sub?: string }) {
  const b = band(score);
  return (
    <div className="grid grid-cols-[minmax(110px,1.2fr)_2fr_52px] items-center gap-3 py-1.5" title={`${label}: ${score.toFixed(1)}%`}>
      <div className="min-w-0"><p className="truncate text-sm">{label}</p>{sub && <p className="truncate text-xs text-white/40">{sub}</p>}</div>
      <div className="h-2.5 overflow-hidden rounded-full bg-white/10">
        <motion.div initial={{ width: 0 }} animate={{ width: `${score}%` }} transition={{ duration: 0.9, ease: "easeOut" }} className="h-full rounded-full" style={{ background: BAND_COLOR[b], boxShadow: `0 0 12px ${BAND_COLOR[b]}88` }} />
      </div>
      <p className="text-right text-sm font-bold tabular-nums">{score.toFixed(1)}%</p>
    </div>
  );
}

function Card({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <motion.section initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass rounded-3xl p-6">
      <h2 className="font-display text-xl font-bold">{title}</h2>
      {subtitle && <p className="mb-4 text-sm text-white/50">{subtitle}</p>}
      {children}
    </motion.section>
  );
}

function TopicGroups({ rows }: { rows: ScoreRow[] }) {
  const groups = useMemo(() => {
    const map = new Map<string, ScoreRow[]>();
    for (const r of rows) {
      const key = `${r.chapter_name || "Unassigned chapter"} / ${r.subject_name || "Subject"}`;
      map.set(key, [...(map.get(key) ?? []), r]);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [rows]);
  const [open, setOpen] = useState<string | null>(groups[0]?.[0] ?? null);
  return (
    <div className="space-y-2">
      {groups.map(([title, topics]) => (
        <div key={title} className="rounded-2xl bg-white/[0.04]">
          <button onClick={() => setOpen(open === title ? null : title)} className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold" aria-expanded={open === title}>
            <span>{title} <span className="text-white/40">· {topics.length} topics</span></span>
            <ChevronDown className={`h-4 w-4 transition ${open === title ? "rotate-180" : ""}`} />
          </button>
          {open === title && (
            <div className="px-4 pb-3">
              {[...topics].sort((a, b) => pct(b) - pct(a)).map((t, i) => <Bar key={i} label={t.name || "Unnamed topic"} score={pct(t)} />)}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [subjectId, setSubjectId] = useState("");
  const [chapterId, setChapterId] = useState("");
  const [period, setPeriod] = useState(0);

  const subjects = useQuery({ queryKey: ["subjects"], queryFn: api.subjects, staleTime: 300_000 });
  const chapters = useQuery({ queryKey: ["chapters", subjectId], queryFn: () => api.chapters(subjectId), enabled: !!subjectId, staleTime: 300_000 });

  const params = useMemo(() => {
    const p: Record<string, string | undefined> = {};
    const days = PERIODS[period].days;
    const today = new Date();
    if (days) {
      p.to_date = iso(today);
      p.from_date = days === "year" ? iso(new Date(today.getFullYear(), 0, 1)) : iso(new Date(today.getTime() - (days - 1) * 86_400_000));
    }
    if (subjectId) p.subject_id = subjectId;
    if (chapterId) p.chapter_id = chapterId;
    return p;
  }, [period, subjectId, chapterId]);

  const { data, isLoading, isError, error } = useQuery({ queryKey: ["analytics", params], queryFn: () => api.analytics(params) });

  const summary = data?.summary ?? {};
  const attempts = data?.attempts_detail ?? [];
  const ordered = useMemo(() => [...attempts].sort((a, b) => String(a.submitted_at ?? "").localeCompare(String(b.submitted_at ?? ""))), [attempts]);
  const count = Number(summary.attempts ?? 0);
  const overall = pct({ score_percentage: summary.score_percentage });
  const delta = ordered.length >= 2 ? pct(ordered[ordered.length - 1]) - pct(ordered[ordered.length - 2]) : null;
  const chart = ordered.map((a: AttemptDetail, i) => ({ n: i + 1, score: pct(a), exam: a.exam_title || "Exam" }));

  const kpis = [
    { label: "Overall score", icon: Percent, color: "text-violet-300", value: count ? <CountUp value={overall} decimals={1} suffix="%" /> : "N/A", note: `${summary.score ?? 0} / ${summary.max_score ?? 0} marks` },
    { label: "Exams taken", icon: ListChecks, color: "text-cyan-brand", value: <CountUp value={count} />, note: "Submitted in this view" },
    { label: "Questions answered", icon: Flame, color: "text-amber-brand", value: <CountUp value={Number(summary.questions_answered ?? 0)} />, note: "Across submitted exams" },
    { label: "Momentum", icon: TrendingUp, color: delta === null || delta >= 0 ? "text-lime-brand" : "text-pink-brand", value: delta === null ? "N/A" : `${delta >= 0 ? "+" : ""}${delta.toFixed(1)} pts`, note: delta === null ? "Take 2 exams to see a trend" : "vs. previous attempt" },
  ];

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">Learning analytics</p>
        <h1 className="font-display text-4xl font-bold">Your <span className="text-gradient">progress</span></h1>
      </header>

      <div className="grid gap-3 sm:grid-cols-3">
        <label className="text-xs font-semibold uppercase tracking-wider text-white/50">Subject
          <select className={`${selectCls} mt-1.5 normal-case tracking-normal`} value={subjectId} onChange={(e) => { setSubjectId(e.target.value); setChapterId(""); }}>
            <option value="" className="bg-ink-900">All subjects</option>
            {(subjects.data ?? []).map((s) => <option key={s.id} value={s.id} className="bg-ink-900">{s.name}</option>)}
          </select>
        </label>
        <label className="text-xs font-semibold uppercase tracking-wider text-white/50">Chapter
          <select className={`${selectCls} mt-1.5 normal-case tracking-normal`} value={chapterId} onChange={(e) => setChapterId(e.target.value)} disabled={!subjectId}>
            <option value="" className="bg-ink-900">All chapters</option>
            {(chapters.data ?? []).map((c) => <option key={c.id} value={c.id} className="bg-ink-900">{c.name}</option>)}
          </select>
        </label>
        <label className="text-xs font-semibold uppercase tracking-wider text-white/50">Period
          <select className={`${selectCls} mt-1.5 normal-case tracking-normal`} value={period} onChange={(e) => setPeriod(Number(e.target.value))}>
            {PERIODS.map((p, i) => <option key={p.label} value={i} className="bg-ink-900">{p.label}</option>)}
          </select>
        </label>
      </div>

      {isError && <ErrorNote message={(error as Error).message} />}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {isLoading ? [0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-32" />) : kpis.map((k, i) => (
          <motion.div key={k.label} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }} whileHover={{ y: -4 }} className="glass rounded-3xl p-5">
            <div className="mb-3 flex items-center justify-between"><p className="text-xs font-semibold uppercase tracking-wider text-white/50">{k.label}</p><k.icon className={`h-5 w-5 ${k.color}`} /></div>
            <p className={`font-display text-3xl font-bold ${k.color}`}>{k.value}</p>
            <p className="mt-1 text-xs text-white/45">{k.note}</p>
          </motion.div>
        ))}
      </div>

      {!isLoading && !isError && attempts.length === 0 && (
        <div className="glass rounded-3xl p-10 text-center">
          <p className="text-5xl">🌱</p>
          <p className="mt-3 font-display text-xl font-bold">Your journey starts here</p>
          <p className="text-white/55">Complete an exam to unlock your analytics.</p>
        </div>
      )}

      {attempts.length > 0 && (
        <>
          <Card title="Progress over attempts" subtitle="The dashed line marks 80% — the 'strong' zone.">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chart} margin={{ top: 10, right: 12, left: -16, bottom: 0 }}>
                  <defs>
                    <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#7c5cff" stopOpacity={0.55} />
                      <stop offset="100%" stopColor="#7c5cff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.07)" vertical={false} />
                  <XAxis dataKey="n" tick={{ fill: "#a8a3d6", fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fill: "#a8a3d6", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <ReferenceLine y={80} stroke="#a3ff6b" strokeDasharray="5 5" strokeOpacity={0.6} />
                  <Tooltip contentStyle={{ background: "#1a1442", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 16, color: "#fff" }} formatter={(v) => [`${Number(v).toFixed(1)}%`, "Score"]} labelFormatter={(l) => chart[Number(l) - 1]?.exam ?? ""} />
                  <Area type="monotone" dataKey="score" stroke="#ff4fa3" strokeWidth={3} fill="url(#fill)" dot={{ r: 5, fill: "#ff4fa3", stroke: "#0b0820", strokeWidth: 2 }} activeDot={{ r: 8 }} animationDuration={1200} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="flex flex-wrap gap-4 text-xs text-white/60">
            {(Object.keys(BAND_LABEL) as (keyof typeof BAND_LABEL)[]).map((k) => (
              <span key={k} className="flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-full" style={{ background: BAND_COLOR[k] }} />{BAND_LABEL[k]}{k === "strong" ? " · 80%+" : k === "good" ? " · 60–79%" : " · under 60%"}</span>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="Subject performance" subtitle="Average score per subject.">
              {(data?.subjects ?? []).length ? [...(data?.subjects ?? [])].sort((a, b) => pct(b) - pct(a)).map((s, i) => <Bar key={i} label={s.name || "Unnamed subject"} score={pct(s)} sub={`${s.attempts ?? 0} attempts`} />) : <p className="text-sm text-white/50">No subject scores for these filters.</p>}
            </Card>
            <Card title="Chapter performance" subtitle="Where you shine and where to focus.">
              {(data?.chapters ?? []).length ? [...(data?.chapters ?? [])].sort((a, b) => (a.subject_name ?? "").localeCompare(b.subject_name ?? "") || pct(a) - pct(b)).map((c, i) => <Bar key={i} label={c.name || "Unnamed chapter"} score={pct(c)} sub={c.subject_name} />) : <p className="text-sm text-white/50">No chapter scores for these filters.</p>}
            </Card>
          </div>

          <Card title="Topic performance" subtitle="Grouped by chapter, strongest first.">
            {(data?.topics ?? []).length ? <TopicGroups key={JSON.stringify(params)} rows={data?.topics ?? []} /> : <p className="text-sm text-white/50">No topic scores for these filters.</p>}
          </Card>

          <Card title="Exam history">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-sm">
                <thead className="text-xs uppercase tracking-wider text-white/40">
                  <tr>{["Exam", "Submitted", "Subject", "Chapter", "Score", "%"].map((h) => <th key={h} className="pb-3 pr-4 font-semibold">{h}</th>)}</tr>
                </thead>
                <tbody>
                  {[...attempts].sort((a, b) => String(b.submitted_at ?? "").localeCompare(String(a.submitted_at ?? ""))).map((a) => (
                    <tr key={a.id} className="border-t border-white/5">
                      <td className="py-3 pr-4 font-semibold">{a.exam_title || "Exam"}</td>
                      <td className="pr-4 text-white/60">{String(a.submitted_at ?? "").slice(0, 19).replace("T", " ")}</td>
                      <td className="pr-4 text-white/60">{(a.subjects ?? []).join(", ")}</td>
                      <td className="pr-4 text-white/60">{(a.chapters ?? []).join(", ")}</td>
                      <td className="pr-4 tabular-nums">{a.score ?? 0} / {a.max_score ?? 0}</td>
                      <td className="font-bold tabular-nums" style={{ color: BAND_COLOR[band(pct(a))] }}>{pct(a).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
