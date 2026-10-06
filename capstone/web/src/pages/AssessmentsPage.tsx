import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { CheckCircle2, Loader2, Rocket, Send } from "lucide-react";
import { CurriculumPicker, formField, formLabel, type CurriculumValue } from "../components/CurriculumPicker";
import { ErrorNote } from "../components/ui";
import { api } from "../lib/api";
import type { CreateExamRequest } from "../lib/types";

function CreateTab({ onCreated }: { onCreated: (examId: string, title: string) => void }) {
  const qc = useQueryClient();
  const [cur, setCur] = useState<CurriculumValue>({ subjectId: "", chapterId: "", topicId: "", ready: false, noChapters: false });
  const [title, setTitle] = useState("Class assessment");
  const [difficulty, setDifficulty] = useState<CreateExamRequest["difficulty"]>("easy");
  const [kind, setKind] = useState<"MCQ" | "Numerical" | "Both">("MCQ");
  const [count, setCount] = useState(5);
  const [minutes, setMinutes] = useState(30);

  const create = useMutation({
    mutationFn: () => api.createExam({
      title,
      subject_id: cur.subjectId,
      chapter_id: cur.chapterId || null,
      difficulty,
      question_types: kind === "Both" ? ["mcq", "numerical"] : kind === "MCQ" ? ["mcq"] : ["numerical"],
      question_count: count,
      time_limit_minutes: minutes,
    }),
    onSuccess: (exam) => { qc.invalidateQueries({ queryKey: ["teacher-exams"] }); onCreated(exam.id, exam.title); },
  });

  return (
    <form onSubmit={(e) => { e.preventDefault(); create.mutate(); }} className="grid gap-5 md:grid-cols-2">
      <CurriculumPicker allChapters onChange={setCur} />
      <label className={`${formLabel} md:col-span-2`}>Exam title
        <input required maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} className={formField} />
      </label>
      <div>
        <p className={formLabel}>Difficulty</p>
        <div className="mt-1.5 grid grid-cols-3 gap-2">
          {(["easy", "medium", "hard"] as const).map((d) => (
            <button type="button" key={d} aria-pressed={difficulty === d} onClick={() => setDifficulty(d)} className={`rounded-2xl border px-3 py-3 text-sm font-semibold capitalize transition ${difficulty === d ? "btn-primary border-transparent" : "border-white/10 bg-white/5 text-white/70 hover:bg-white/10"}`}>{d}</button>
          ))}
        </div>
      </div>
      <div>
        <p className={formLabel}>Question type</p>
        <div className="mt-1.5 grid grid-cols-3 gap-2">
          {(["MCQ", "Numerical", "Both"] as const).map((k) => (
            <button type="button" key={k} aria-pressed={kind === k} onClick={() => setKind(k)} className={`rounded-2xl border px-3 py-3 text-sm font-semibold transition ${kind === k ? "border-cyan-brand bg-cyan-brand/15 text-cyan-brand" : "border-white/10 bg-white/5 text-white/60 hover:bg-white/10"}`}>{k}</button>
          ))}
        </div>
      </div>
      <label className={formLabel}>Number of questions: <span className="text-white">{count}</span>
        <input type="range" min={1} max={20} value={count} onChange={(e) => setCount(Number(e.target.value))} className="mt-3 w-full accent-pink-500" />
      </label>
      <label className={formLabel}>Time limit: <span className="text-white">{minutes} min</span>
        <input type="range" min={1} max={180} value={minutes} onChange={(e) => setMinutes(Number(e.target.value))} className="mt-3 w-full accent-violet-500" />
      </label>
      <div className="md:col-span-2">
        {create.isError && <div className="mb-3"><ErrorNote message={(create.error as Error).message} /></div>}
        <button disabled={create.isPending || !cur.ready} className="btn-primary flex w-full items-center justify-center gap-2 rounded-2xl py-4 font-bold">
          {create.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Rocket className="h-5 w-5" />}
          {create.isPending ? "Creating assessment… this can take a moment" : "Create assessment"}
        </button>
      </div>
    </form>
  );
}

function AssignTab({ preselect }: { preselect: string }) {
  const exams = useQuery({ queryKey: ["teacher-exams"], queryFn: api.teacherExams });
  const roster = useQuery({ queryKey: ["roster"], queryFn: api.roster });
  const qc = useQueryClient();
  const [examId, setExamId] = useState(preselect);
  const [picked, setPicked] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [done, setDone] = useState("");

  const assign = useMutation({
    mutationFn: () => api.assignExam(examId || exams.data![0].id, picked),
    onSuccess: (r) => { setDone(`Assessment assigned to ${r.length} student(s).`); setPicked([]); qc.invalidateQueries({ queryKey: ["teacher-dashboard"] }); },
  });

  if (exams.isLoading || roster.isLoading) return <p className="text-white/50">Loading…</p>;
  if (exams.isError) return <ErrorNote message={(exams.error as Error).message} />;
  if (!exams.data?.length) return <p className="text-sm text-white/55">Create an assessment before assigning it.</p>;
  if (!roster.data?.length) return <p className="text-sm text-white/55">Add students to your roster before assigning assessments.</p>;

  const effectiveExam = examId || exams.data[0].id;
  const toggle = (id: string) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));

  return (
    <form onSubmit={(e) => { e.preventDefault(); setDone(""); if (picked.length === 0) { setError("Select at least one student."); return; } setError(""); assign.mutate(); }} className="space-y-5">
      <label className={formLabel}>Assessment
        <select className={formField} value={effectiveExam} onChange={(e) => setExamId(e.target.value)}>
          {exams.data.map((x) => <option key={x.id} value={x.id} className="bg-ink-900">{x.title} · {x.id.slice(0, 8)}</option>)}
        </select>
      </label>
      <div>
        <div className="flex items-center justify-between"><p className={formLabel}>Students ({picked.length} selected)</p>
          <button type="button" className="text-xs text-cyan-brand hover:underline" onClick={() => setPicked(picked.length === roster.data!.length ? [] : roster.data!.map((s) => s.id))}>{picked.length === roster.data.length ? "Clear all" : "Select all"}</button></div>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          {roster.data.map((s) => {
            const on = picked.includes(s.id);
            return (
              <button type="button" key={s.id} role="checkbox" aria-checked={on} onClick={() => toggle(s.id)} className={`flex items-center gap-3 rounded-2xl border p-3 text-left transition ${on ? "border-violet-brand bg-violet-brand/20" : "border-white/10 bg-white/[0.04] hover:border-white/25"}`}>
                <span className={`grid h-9 w-9 place-items-center rounded-xl text-sm font-bold ${on ? "btn-primary" : "bg-white/10"}`}>{on ? <CheckCircle2 className="h-4 w-4" /> : s.full_name.charAt(0).toUpperCase()}</span>
                <span className="min-w-0"><span className="block truncate text-sm font-semibold">{s.full_name}</span><span className="block truncate text-xs text-white/50">{s.email}</span></span>
              </button>
            );
          })}
        </div>
      </div>
      {error && <ErrorNote message={error} />}
      {assign.isError && <ErrorNote message={(assign.error as Error).message} />}
      {done && <p role="status" className="rounded-2xl bg-lime-brand/15 px-4 py-3 text-sm text-lime-brand">{done}</p>}
      <button disabled={assign.isPending} className="btn-primary flex w-full items-center justify-center gap-2 rounded-2xl py-4 font-bold">
        {assign.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}Assign assessment
      </button>
    </form>
  );
}

export default function AssessmentsPage() {
  const [tab, setTab] = useState<"create" | "assign">("create");
  const [created, setCreated] = useState<{ id: string; title: string } | null>(null);
  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">Assessments</p>
        <h1 className="font-display text-4xl font-bold">Create &amp; <span className="text-gradient">assign</span></h1>
        <p className="text-white/55">Create an assessment, then assign it to students in your roster.</p>
      </header>
      <div role="tablist" className="glass inline-flex rounded-2xl p-1">
        {([["create", "Create Assessment"], ["assign", "Assign Assessment"]] as const).map(([k, l]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)} className={`relative rounded-xl px-5 py-2.5 text-sm font-semibold transition ${tab === k ? "btn-primary" : "text-white/60 hover:text-white"}`}>{l}</button>
        ))}
      </div>
        {created && tab === "create" && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-lime-brand/15 px-5 py-4 text-lime-brand">
            <span>Assessment ‘{created.title}’ created successfully.</span>
            <button onClick={() => setTab("assign")} className="btn-primary rounded-xl px-4 py-2 text-sm font-bold text-white">Proceed to Assign Assessment</button>
          </motion.div>
        )}
      <section className="glass rounded-3xl p-6 sm:p-8">
        {tab === "create" ? <CreateTab onCreated={(id, title) => setCreated({ id, title })} /> : <AssignTab preselect={created?.id ?? ""} />}
      </section>
    </div>
  );
}
