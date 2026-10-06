import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { BookOpen, ClipboardList, Sparkles, Users } from "lucide-react";
import { CountUp, ErrorNote, Skeleton } from "../components/ui";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

const avg = (v: number | string | null | undefined) => (v === null || v === undefined ? "N/A" : `${Number(v).toFixed(1)}%`);

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="glass rounded-3xl p-5">
      <p className="text-xs font-semibold uppercase tracking-wider text-white/50">{label}</p>
      <p className="mt-2 font-display text-4xl font-bold" style={{ color }}><CountUp value={value} /></p>
    </div>
  );
}

const TILES = [
  { to: "/roster", icon: Users, title: "Student roster", text: "Add and find your students.", color: "from-cyan-brand to-violet-brand" },
  { to: "/assessments", icon: ClipboardList, title: "Assessments", text: "Create exams and assign them.", color: "from-violet-brand to-pink-brand" },
  { to: "/questions", icon: BookOpen, title: "Question bank", text: "Browse and review questions.", color: "from-pink-brand to-amber-brand" },
  { to: "/generate", icon: Sparkles, title: "Generate questions", text: "Fill the bank with AI questions.", color: "from-lime-brand to-cyan-brand" },
];

export default function TeacherHomePage() {
  const { user } = useAuth();
  const q = useQuery({ queryKey: ["teacher-dashboard"], queryFn: api.teacherDashboard });
  const d = q.data;
  return (
    <div className="space-y-8">
      <header>
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">Teacher hub</p>
        <h1 className="font-display text-4xl font-bold">Welcome, <span className="text-gradient">{user?.full_name?.split(" ")[0] ?? "teacher"}</span></h1>
        <p className="text-white/55">Your workspace for student progress, assessments and learning content.</p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {TILES.map((t, i) => (
          <motion.div key={t.to} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }} whileHover={{ y: -5 }}>
            <Link to={t.to} className="glass block h-full rounded-3xl p-5">
              <span className={`mb-3 grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br ${t.color} text-ink-950`}><t.icon className="h-5 w-5" /></span>
              <p className="font-display text-lg font-bold">{t.title}</p>
              <p className="text-sm text-white/50">{t.text}</p>
            </Link>
          </motion.div>
        ))}
      </div>

      {q.isLoading && <Skeleton className="h-48" />}
      {q.isError && <ErrorNote message={(q.error as Error).message} />}
      {d && (
        <>
          <section>
            <h2 className="mb-3 font-display text-2xl font-bold">Question bank</h2>
            <div className="grid gap-4 sm:grid-cols-3">
              <Stat label="Validated" value={d.questions.validated} color="#a3ff6b" />
              <Stat label="Generated" value={d.questions.generated} color="#22d3ee" />
              <Stat label="Rejected" value={d.questions.rejected} color="#ff4fa3" />
            </div>
          </section>
          <section>
            <h2 className="mb-3 font-display text-2xl font-bold">Assessment analytics</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Stat label="Assigned" value={d.assignments.total} color="#7c5cff" />
              <Stat label="Started" value={d.assignments.started} color="#ffc247" />
              <Stat label="Completed" value={d.assignments.completed} color="#a3ff6b" />
              <div className="glass rounded-3xl p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-white/50">Average score</p>
                <p className="mt-2 font-display text-4xl font-bold">{avg(d.assignments.average_score_percentage)}</p>
              </div>
            </div>
          </section>
          <section className="glass overflow-x-auto rounded-3xl p-6">
            <h2 className="mb-4 font-display text-xl font-bold">Exam records</h2>
            {d.exam_performance.length === 0 ? <p className="text-sm text-white/55">Exam records will appear here after you assign an assessment.</p> : (
              <table className="w-full min-w-[480px] text-left text-sm">
                <thead className="text-xs uppercase tracking-wider text-white/45"><tr><th className="pb-2">Exam</th><th>Assigned</th><th>Started</th><th>Completed</th><th>Average score</th></tr></thead>
                <tbody>
                  {d.exam_performance.map((e, i) => (
                    <tr key={`${e.title}-${i}`} className="border-t border-white/10"><td className="py-3 font-semibold">{e.title}</td><td>{e.assigned}</td><td>{e.started}</td><td>{e.completed}</td><td>{avg(e.average_score_percentage)}</td></tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </div>
  );
}
