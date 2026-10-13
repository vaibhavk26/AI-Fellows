import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown } from "lucide-react";
import { CurriculumPicker, formField, formLabel, type CurriculumValue } from "../components/CurriculumPicker";
import { Dropdown, ErrorNote, Skeleton } from "../components/ui";
import { api } from "../lib/api";

const PAGE = 10;
const STATUS_COLOR: Record<string, string> = { validated: "bg-lime-brand/15 text-lime-brand", generated: "bg-cyan-brand/15 text-cyan-brand", rejected: "bg-pink-brand/15 text-pink-300" };

export default function QuestionBankPage() {
  const questions = useQuery({ queryKey: ["bank"], queryFn: api.questions });
  const subjects = useQuery({ queryKey: ["subjects"], queryFn: api.subjects, staleTime: 300_000 });
  const [cur, setCur] = useState<CurriculumValue>({ subjectId: "", chapterId: "", topicId: "", ready: true, noChapters: false });
  const [difficulty, setDifficulty] = useState("");
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState<string | null>(null);

  const filtered = useMemo(() => (questions.data ?? []).filter((q) =>
    (!cur.subjectId || q.subject_id === cur.subjectId) && (!cur.chapterId || q.chapter_id === cur.chapterId) && (!cur.topicId || q.topic_id === cur.topicId) &&
    (!difficulty || q.difficulty === difficulty) && (!type || q.question_type === type) && (!status || q.status === status)), [questions.data, cur, difficulty, type, status]);

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE));
  const current = Math.min(page, pages);
  const visible = filtered.slice((current - 1) * PAGE, current * PAGE);
  const subjectName = (id: string) => subjects.data?.find((s) => s.id === id)?.name ?? "Subject";
  const reset = <T,>(set: (v: T) => void) => (v: T) => { set(v); setPage(1); };
  const onCur = useMemo(() => (v: CurriculumValue) => { setCur(v); setPage(1); }, []);

  const select = (label: string, value: string, set: (v: string) => void, all: string, opts: string[]) => (
    <label className={formLabel}>{label}
      <Dropdown
        className={formField}
        value={value}
        onChange={(selected) => reset(set)(selected)}
        options={[{ value: "", label: all }, ...opts.map((option) => ({ value: option, label: option }))]}
      />
    </label>
  );

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">Question bank</p>
        <h1 className="font-display text-4xl font-bold">Browse <span className="text-gradient">questions</span></h1>
        <p className="text-white/55">Filter generated questions and open a card to review its answer and learning objective.</p>
      </header>

      <section className="glass grid gap-4 rounded-3xl p-5 sm:grid-cols-2 lg:grid-cols-3">
        <CurriculumPicker allSubjects showTopic onChange={onCur} />
        {select("Difficulty", difficulty, setDifficulty, "All difficulties", ["easy", "medium", "hard"])}
        {select("Question type", type, setType, "All types", ["mcq", "numerical"])}
        {select("Status", status, setStatus, "All statuses", ["validated", "generated", "rejected"])}
      </section>

      {questions.isLoading && <Skeleton className="h-64" />}
      {questions.isError && <ErrorNote message={(questions.error as Error).message} />}
      {questions.isSuccess && (
        <>
          <p className="text-sm text-white/50">{filtered.length} questions match these filters</p>
          {visible.length === 0 && <div className="glass rounded-3xl p-8 text-center text-white/55">No questions match these filters.</div>}
          <div className="space-y-3">
            {visible.map((q) => {
              const isOpen = open === q.id;
              return (
                <article key={q.id} className="glass overflow-hidden rounded-3xl">
                  <button onClick={() => setOpen(isOpen ? null : q.id)} aria-expanded={isOpen} className="flex w-full items-center gap-3 p-4 text-left">
                    <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-bold capitalize ${STATUS_COLOR[q.status] ?? "bg-white/10"}`}>{q.status}</span>
                    <span className="shrink-0 text-xs font-semibold uppercase text-white/45">{q.question_type} · {q.difficulty}</span>
                    <span className="min-w-0 flex-1 truncate">{q.question_text}</span>
                    <ChevronDown className={`h-5 w-5 shrink-0 transition ${isOpen ? "rotate-180" : ""}`} />
                  </button>
                  {isOpen && (
                    <div className="space-y-2 border-t border-white/10 p-5 text-sm">
                      <p className="font-semibold">{q.question_text}</p>
                      {(q.options ?? []).map((o) => <p key={o.key} className="text-white/70">{o.key}. {o.text}</p>)}
                      <p><span className="font-semibold text-lime-brand">Expected answer:</span> {q.expected_answer}</p>
                      <p className="text-white/70">{q.explanation}</p>
                      <p className="text-xs text-white/45">Learning objective: {q.learning_objective}</p>
                      <p className="text-xs text-white/45">{subjectName(q.subject_id)} · {q.marks} marks</p>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
          {filtered.length > PAGE && (
            <div className="flex items-center justify-center gap-3">
              <button disabled={current <= 1} onClick={() => setPage(current - 1)} className="rounded-xl bg-white/10 px-4 py-2 text-sm disabled:opacity-30">Previous</button>
              <span className="text-sm text-white/60">Page {current} of {pages}</span>
              <button disabled={current >= pages} onClick={() => setPage(current + 1)} className="rounded-xl bg-white/10 px-4 py-2 text-sm disabled:opacity-30">Next</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
