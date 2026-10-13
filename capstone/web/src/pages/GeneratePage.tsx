import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Loader2, Sparkles } from "lucide-react";
import { CurriculumPicker, formField, formLabel, type CurriculumValue } from "../components/CurriculumPicker";
import { Dropdown, ErrorNote } from "../components/ui";
import { ApiError, api } from "../lib/api";
import type { GenerateQuestionsRequest } from "../lib/types";

export default function GeneratePage() {
  const [cur, setCur] = useState<CurriculumValue>({ subjectId: "", chapterId: "", topicId: "", ready: false, noChapters: false });
  const [type, setType] = useState<GenerateQuestionsRequest["question_type"]>("mcq");
  const [difficulty, setDifficulty] = useState<GenerateQuestionsRequest["difficulty"]>("easy");
  const [marks, setMarks] = useState(1);
  const [count, setCount] = useState(5);
  const [bloom, setBloom] = useState<GenerateQuestionsRequest["bloom_level"]>("remember");

  const gen = useMutation({
    mutationFn: () => api.generateQuestions({
      subject_id: cur.subjectId, chapter_id: cur.chapterId, topic_id: cur.topicId || null,
      difficulty, question_type: type, marks, number_of_questions: count, bloom_level: bloom,
    }),
  });

  const err = gen.error instanceof ApiError && gen.error.status === 429
    ? "The question generator is busy right now (AI provider rate limit). Please wait about a minute and try again, or generate fewer questions."
    : gen.error ? (gen.error as Error).message : "";

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">AI studio</p>
        <h1 className="font-display text-4xl font-bold">Generate <span className="text-gradient">questions</span></h1>
      </header>
      <form onSubmit={(e) => { e.preventDefault(); gen.mutate(); }} className="glass grid gap-5 rounded-3xl p-6 sm:p-8 md:grid-cols-2">
        <CurriculumPicker showTopic onChange={setCur} />
        <label className={formLabel}>Question type
          <Dropdown className={formField} value={type} onChange={(value) => setType(value as typeof type)} options={[{ value: "mcq", label: "mcq" }, { value: "numerical", label: "numerical" }]} />
        </label>
        <label className={formLabel}>Difficulty
          <Dropdown className={formField} value={difficulty} onChange={(value) => setDifficulty(value as typeof difficulty)} options={["easy", "medium", "hard"].map((d) => ({ value: d, label: d }))} />
        </label>
        <label className={formLabel}>Marks
          <input type="number" min={1} max={10} value={marks} onChange={(e) => setMarks(Math.max(1, Math.min(10, Number(e.target.value) || 1)))} className={formField} />
        </label>
        <label className={formLabel}>Learning level
          <Dropdown className={formField} value={bloom} onChange={(value) => setBloom(value as typeof bloom)} options={["remember", "understand", "apply", "analyze"].map((d) => ({ value: d, label: d }))} />
        </label>
        <label className={`${formLabel} md:col-span-2`}>Questions: <span className="text-white">{count}</span>
          <input type="range" min={1} max={10} value={count} onChange={(e) => setCount(Number(e.target.value))} className="mt-3 w-full accent-pink-500" />
        </label>
        <div className="md:col-span-2">
          {cur.noChapters && <div className="mb-3"><ErrorNote message="Select a valid chapter before generating questions." /></div>}
          <motion.button whileTap={{ scale: 0.98 }} disabled={gen.isPending || !cur.ready} className="btn-primary flex w-full items-center justify-center gap-2 rounded-2xl py-4 font-bold">
            {gen.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Sparkles className="h-5 w-5" />}
            {gen.isPending ? "Generating questions… this can take up to a minute" : "Generate"}
          </motion.button>
        </div>
      </form>

      {err && <ErrorNote message={err} />}
      {gen.isSuccess && (
        <section className="glass rounded-3xl p-6">
          <p role="status" className="mb-4 rounded-2xl bg-lime-brand/15 px-4 py-3 text-lime-brand">Generated {gen.data.meta.validated} validated question(s).</p>
          <ul className="space-y-3">
            {gen.data.data.questions.map((q, i) => (
              <li key={i} className="rounded-2xl bg-white/[0.04] p-4">
                <p>{q.question_text}</p>
                <p className="mt-1 text-xs text-white/50">{q.status} · {q.difficulty} · {q.marks} mark(s)</p>
                {q.status === "rejected" && <p className="mt-2 text-sm text-pink-300">Rejection reason(s): {(q.rejection_reasons?.length ? q.rejection_reasons : ["No rejection reason was recorded."]).join("; ")}</p>}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
