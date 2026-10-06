import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Link } from "react-router-dom";
import { CheckCircle2, Clock, Loader2, Play, Rocket, Zap } from "lucide-react";
import { Dropdown, ErrorNote, Skeleton } from "../../components/ui";
import { api } from "../../lib/api";
import type { Assignment, AttemptStart, Exam, GenerateExamRequest } from "../../lib/types";

const fieldCls = "mt-1.5 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm normal-case tracking-normal text-white outline-none transition focus:border-violet-brand focus:ring-4 focus:ring-violet-brand/20 disabled:opacity-50";
const labelCls = "text-xs font-semibold uppercase tracking-wider text-white/50";
const LOADING_LINES = ["Reading your curriculum…", "Crafting fresh questions…", "Checking answers & explanations…", "Polishing your quest…"];

export interface ActiveExam { exam: Exam; attempt: AttemptStart }

function GeneratingOverlay() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((n) => (n + 1) % LOADING_LINES.length), 2200);
    return () => clearInterval(t);
  }, []);
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="fixed inset-0 z-50 grid place-items-center bg-ink-950/85 backdrop-blur-md" role="status" aria-live="polite">
      <div className="text-center">
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2.4, ease: "linear" }} className="btn-primary mx-auto grid h-20 w-20 place-items-center rounded-3xl">
          <Zap className="h-10 w-10" fill="white" />
        </motion.div>
        <p className="mt-6 font-display text-2xl font-bold">Building your exam</p>
        <AnimatePresence mode="wait">
          <motion.p key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="mt-2 text-white/60">{LOADING_LINES[i]}</motion.p>
        </AnimatePresence>
        <p className="mt-6 text-xs text-white/35">AI generation can take a little while — hang tight.</p>
      </div>
    </motion.div>
  );
}

export default function ExamSetup({ onStart, autoStartId, onAutoStarted }: { onStart: (active: ActiveExam) => void; autoStartId?: string | null; onAutoStarted?: () => void }) {
  const qc = useQueryClient();
  const assignments = useQuery({ queryKey: ["assignments"], queryFn: api.assignments });
  const subjects = useQuery({ queryKey: ["subjects"], queryFn: api.subjects, staleTime: 300_000 });

  const [subjectId, setSubjectId] = useState("");
  const [chapterId, setChapterId] = useState("");
  const [topicId, setTopicId] = useState("");
  const [difficulty, setDifficulty] = useState<GenerateExamRequest["difficulty"]>("easy");
  const [types, setTypes] = useState<GenerateExamRequest["question_types"]>(["mcq"]);
  const [count, setCount] = useState(5);
  const [minutes, setMinutes] = useState(20);
  const [formError, setFormError] = useState("");

  const activeSubject = subjectId || subjects.data?.[0]?.id || "";
  const chapters = useQuery({ queryKey: ["chapters", activeSubject], queryFn: () => api.chapters(activeSubject), enabled: !!activeSubject, staleTime: 300_000 });
  const activeChapter = chapterId && chapters.data?.some((c) => c.id === chapterId) ? chapterId : chapters.data?.[0]?.id ?? "";
  const topics = useQuery({ queryKey: ["topics", activeChapter], queryFn: () => api.topics(activeChapter), enabled: !!activeChapter, staleTime: 300_000 });

  const [ready, setReady] = useState<number | null>(null);
  const begin = useMutation({
    mutationFn: async (job: { kind: "assigned"; assignment: Assignment } | { kind: "practice"; body: GenerateExamRequest }) => {
      const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (!calm) {
        for (const n of [3, 2, 1]) { setReady(n); await new Promise((r) => setTimeout(r, 800)); }
      }
      setReady(null);
      const exam = job.kind === "assigned" ? await api.getExam(job.assignment.exam_id) : await api.generateExam(job.body);
      const attempt = await api.startAttempt(exam.id);
      return { exam, attempt };
    },
    onError: () => setReady(null),
    onSuccess: (active) => { qc.invalidateQueries({ queryKey: ["assignments"] }); onStart(active); },
  });

  const autoStarted = useRef(false);
  useEffect(() => {
    if (!autoStartId || autoStarted.current || !assignments.data) return;
    autoStarted.current = true;
    onAutoStarted?.();
    const match = assignments.data.find((x) => x.id === autoStartId && x.status !== "completed");
    if (match) begin.mutate({ kind: "assigned", assignment: match });
  }, [autoStartId, assignments.data, begin, onAutoStarted]);

  const toggleType = (t: "mcq" | "numerical") => setTypes((cur) => (cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]));

  function generate(e: React.FormEvent) {
    e.preventDefault();
    if (types.length === 0) { setFormError("Select at least one question type."); return; }
    setFormError("");
    begin.mutate({
      kind: "practice",
      body: { subject_id: activeSubject, chapter_id: activeChapter || null, topic_id: topicId && topics.data?.some((t) => t.id === topicId) ? topicId : null, difficulty, question_types: types, question_count: count, time_limit_minutes: minutes },
    });
  }

  const noCurriculum = subjects.isSuccess && subjects.data.length === 0;

  return (
    <div className="space-y-8">
      {begin.isPending && <GeneratingOverlay />}
      <header>
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">Choose your challenge</p>
        <h1 className="font-display text-4xl font-bold">Pick a <span className="text-gradient">quest</span></h1>
      </header>
      {begin.isError && <ErrorNote message={(begin.error as Error).message} />}

      <section>
        <h2 className="mb-3 font-display text-2xl font-bold">Assigned exams</h2>
        {assignments.isLoading ? <Skeleton className="h-28" /> : assignments.isError ? <ErrorNote message={(assignments.error as Error).message} /> : (assignments.data ?? []).length === 0 ? (
          <div className="glass rounded-3xl p-6 text-sm text-white/55">Nothing assigned by your teacher yet — try a practice exam below.</div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {(assignments.data ?? []).map((a) => {
              const done = a.status === "completed";
              return (
                <motion.div key={a.id} whileHover={{ y: done ? 0 : -4 }} className="glass flex items-center justify-between gap-4 rounded-3xl p-5">
                  <div className="min-w-0">
                    <p className="truncate font-display text-lg font-bold">{a.exam_title}</p>
                    <p className="mt-1 flex items-center gap-2 text-xs text-white/50"><Clock className="h-3.5 w-3.5" />{a.question_count} questions · {a.time_limit_minutes ?? "—"} min · <span className="capitalize">{a.status}</span></p>
                  </div>
                  {done ? (
                    <span className="flex items-center gap-1.5 rounded-2xl bg-lime-brand/15 px-4 py-2.5 text-sm font-bold text-lime-brand"><CheckCircle2 className="h-4 w-4" />Completed</span>
                  ) : (
                    <button disabled={begin.isPending} onClick={() => begin.mutate({ kind: "assigned", assignment: a })} className="btn-primary flex shrink-0 items-center gap-2 rounded-2xl px-5 py-2.5 text-sm font-bold">
                      <Play className="h-4 w-4" fill="white" />{a.status === "assigned" ? "Start" : "Resume"}
                    </button>
                  )}
                </motion.div>
              );
            })}
          </div>
        )}
      </section>

      <section className="glass rounded-3xl p-6 sm:p-8">
        <h2 className="font-display text-2xl font-bold">Start a practice exam</h2>
        <p className="mb-6 text-sm text-white/50">Tune the difficulty and we'll build a fresh set just for you.</p>
        {noCurriculum && <ErrorNote message="No curriculum has been ingested yet." />}
        {subjects.isError && <ErrorNote message={(subjects.error as Error).message} />}
        {!noCurriculum && (
          <form onSubmit={generate} className="grid gap-5 md:grid-cols-2">
            <label className={labelCls}>Subject
              <Dropdown
                className={fieldCls}
                value={activeSubject}
                onChange={(value) => { setSubjectId(value); setChapterId(""); setTopicId(""); }}
                options={(subjects.data ?? []).map((s) => ({ value: s.id, label: s.name }))}
              />
            </label>
            <label className={labelCls}>Chapter
              <Dropdown
                className={fieldCls}
                value={activeChapter}
                disabled={!chapters.data?.length}
                onChange={(value) => { setChapterId(value); setTopicId(""); }}
                options={(chapters.data ?? []).map((c) => ({ value: c.id, label: c.name }))}
              />
              {chapters.isSuccess && chapters.data.length === 0 && <span className="mt-1 block text-xs normal-case tracking-normal text-white/45">No chapters available for this subject.</span>}
            </label>
            <label className={labelCls}>Topic
              <Dropdown
                className={fieldCls}
                value={topicId}
                disabled={!activeChapter}
                onChange={setTopicId}
                options={[{ value: "", label: "All topics" }, ...(topics.data ?? []).map((t) => ({ value: t.id, label: t.name }))]}
              />
            </label>
            <div>
              <p className={labelCls}>Difficulty</p>
              <div className="mt-1.5 grid grid-cols-3 gap-2" role="radiogroup" aria-label="Difficulty">
                {([["easy", "🌱 Easy"], ["medium", "🔥 Medium"], ["hard", "💀 Hard"]] as const).map(([d, label]) => (
                  <button type="button" key={d} role="radio" aria-checked={difficulty === d} onClick={() => setDifficulty(d)} className={`rounded-2xl border px-3 py-3 text-sm font-semibold transition ${difficulty === d ? "btn-primary border-transparent" : "border-white/10 bg-white/5 text-white/70 hover:bg-white/10"}`}>{label}</button>
                ))}
              </div>
            </div>
            <div>
              <p className={labelCls}>Question types</p>
              <div className="mt-1.5 flex gap-2">
                {(["mcq", "numerical"] as const).map((t) => (
                  <button type="button" key={t} aria-pressed={types.includes(t)} onClick={() => toggleType(t)} className={`flex-1 rounded-2xl border px-3 py-3 text-sm font-semibold transition ${types.includes(t) ? "border-cyan-brand bg-cyan-brand/15 text-cyan-brand" : "border-white/10 bg-white/5 text-white/60 hover:bg-white/10"}`}>{t === "mcq" ? "Multiple choice" : "Numerical"}</button>
                ))}
              </div>
            </div>
            <label className={labelCls}>Questions: <span className="text-white">{count}</span>
              <input type="range" min={1} max={20} value={count} onChange={(e) => setCount(Number(e.target.value))} className="mt-3 w-full accent-pink-500" />
            </label>
            <label className={labelCls}>Time limit: <span className="text-white">{minutes} min</span>
              <input type="range" min={1} max={60} value={minutes} onChange={(e) => setMinutes(Number(e.target.value))} className="mt-3 w-full accent-violet-500" />
            </label>
            <div className="md:col-span-2">
              {formError && <div className="mb-3"><ErrorNote message={formError} /></div>}
              <motion.button whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.98 }} disabled={begin.isPending || !activeSubject} type="submit" className="btn-primary flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-base font-bold">
                {begin.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Rocket className="h-5 w-5" />}Generate exam
              </motion.button>
            </div>
          </form>
        )}
      </section>
      <p className="text-center text-xs text-white/35">Finished one? <Link className="underline hover:text-white/70" to="/results">Review your results</Link></p>
      {ready !== null && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink-950/90 backdrop-blur-sm" role="status" aria-live="assertive">
          <div className="text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">Get ready</p>
            <p key={ready} className="font-display text-9xl font-bold text-gradient">{ready}</p>
            <p className="mt-2 text-white/60">Your timer starts right after.</p>
          </div>
        </div>
      )}
    </div>
  );
}
