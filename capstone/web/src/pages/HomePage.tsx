import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import confetti from "canvas-confetti";
import { useEffect } from "react";
import { ArrowRight, Clock, Flame, PlayCircle, Star, Swords } from "lucide-react";
import { CountUp, ErrorNote, ProgressRing, Skeleton } from "../components/ui";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { computeBadges, computeStreak, computeXp, greeting, levelFromXp, pct } from "../lib/gamify";

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0 } };

export default function HomePage() {
  const { user } = useAuth();
  const analytics = useQuery({ queryKey: ["analytics", {}], queryFn: () => api.analytics({}) });
  const assignments = useQuery({ queryKey: ["assignments"], queryFn: api.assignments });

  const attempts = analytics.data?.attempts_detail ?? [];
  const summary = analytics.data?.summary ?? {};
  const xp = computeXp(Number(summary.questions_answered ?? 0), Number(summary.score ?? 0));
  const lvl = levelFromXp(xp);
  const streak = computeStreak(attempts);
  const badges = computeBadges(attempts, streak, analytics.data?.topics ?? []);
  const latest = [...attempts].sort((a, b) => String(b.submitted_at).localeCompare(String(a.submitted_at)))[0];

  useEffect(() => {
    if (latest && pct(latest) >= 90 && !sessionStorage.getItem("examiq.confetti")) {
      sessionStorage.setItem("examiq.confetti", "1");
      confetti({ particleCount: 140, spread: 80, origin: { y: 0.35 }, colors: ["#7c5cff", "#ff4fa3", "#ffc247", "#22d3ee", "#a3ff6b"] });
    }
  }, [latest]);

  const pending = (assignments.data ?? []).filter((a) => a.status !== "completed");
  const firstName = user?.full_name.split(" ")[0] ?? "there";

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.header variants={item}>
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">{greeting()}</p>
        <h1 className="font-display text-4xl font-bold md:text-5xl">Ready to level up, <span className="text-gradient">{firstName}</span>?</h1>
      </motion.header>

      {analytics.isError && <ErrorNote message={(analytics.error as Error).message} />}

      <div className="grid gap-5 lg:grid-cols-3">
        <motion.div variants={item} className="glass relative overflow-hidden rounded-3xl p-6 lg:col-span-2">
          <div className="absolute -right-10 -top-10 h-48 w-48 rounded-full bg-violet-brand/30 blur-3xl" />
          {analytics.isLoading ? <Skeleton className="h-40" /> : (
            <div className="relative flex flex-col items-center gap-6 sm:flex-row">
              <button onClick={() => confetti({ particleCount: 90, spread: 70, origin: { y: 0.6 } })} aria-label={`Level ${lvl.level}`} className="rounded-full transition hover:scale-105">
                <ProgressRing value={lvl.progress * 100} size={150}>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-widest text-white/50">Level</p>
                    <p className="font-display text-5xl font-bold"><CountUp value={lvl.level} /></p>
                  </div>
                </ProgressRing>
              </button>
              <div className="flex-1 text-center sm:text-left">
                <p className="font-display text-3xl font-bold"><CountUp value={xp} /> <span className="text-lg text-white/50">XP</span></p>
                <p className="mt-1 text-sm text-white/60">{Math.max(0, lvl.next - xp)} XP to Level {lvl.level + 1}</p>
                <div className="mt-4 flex flex-wrap justify-center gap-3 sm:justify-start">
                  <span className="flex items-center gap-2 rounded-full bg-amber-brand/15 px-4 py-2 text-sm font-bold text-amber-brand">
                    <Flame className="h-4 w-4" fill="currentColor" /> {streak}-day streak
                  </span>
                  <span className="flex items-center gap-2 rounded-full bg-cyan-brand/15 px-4 py-2 text-sm font-bold text-cyan-brand">
                    <Star className="h-4 w-4" fill="currentColor" /> {badges.filter((b) => b.earned).length}/{badges.length} badges
                  </span>
                </div>
              </div>
            </div>
          )}
        </motion.div>

        <motion.div variants={item} className="glass rounded-3xl p-6">
          <h2 className="mb-4 font-display text-lg font-bold">Badges</h2>
          <div className="grid grid-cols-5 gap-2">
            {badges.map((b) => (
              <motion.div key={b.id} whileHover={{ scale: 1.15, rotate: -4 }} title={`${b.label} — ${b.hint}`} className={`grid aspect-square place-items-center rounded-2xl text-2xl ${b.earned ? "bg-white/10" : "bg-white/[0.03] opacity-35 grayscale"}`}>
                {b.emoji}
              </motion.div>
            ))}
          </div>
          <p className="mt-4 text-xs text-white/50">Hover a badge to see how to earn it.</p>
        </motion.div>
      </div>

      <motion.section variants={item}>
        <div className="mb-3 flex items-center gap-2">
          <Swords className="h-5 w-5 text-pink-brand" />
          <h2 className="font-display text-2xl font-bold">Your quests</h2>
        </div>
        {assignments.isLoading ? <Skeleton className="h-32" /> : assignments.isError ? <ErrorNote message={(assignments.error as Error).message} /> : pending.length === 0 ? (
          <div className="glass rounded-3xl p-8 text-center text-white/60">No exams assigned right now. Enjoy the break — or review your progress! 🎉</div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {pending.map((a) => (
              <motion.div key={a.id} whileHover={{ y: -6 }} className="glass group rounded-3xl p-5">
                <div className="mb-3 flex items-center justify-between text-xs font-semibold uppercase tracking-wider">
                  <span className="rounded-full bg-violet-brand/25 px-3 py-1 text-violet-200">{a.status}</span>
                  <span className="flex items-center gap-1 text-white/50"><Clock className="h-3.5 w-3.5" />{a.time_limit_minutes ? `${a.time_limit_minutes} min` : "Untimed"}</span>
                </div>
                <h3 className="font-display text-xl font-bold">{a.exam_title}</h3>
                <p className="mb-5 mt-1 text-sm text-white/55">{a.question_count} questions · +{a.question_count * 10} XP</p>
                <Link to={`/exam?assignment=${a.id}`} className="btn-primary flex items-center justify-center gap-2 rounded-2xl py-3 text-sm font-bold">
                  <PlayCircle className="h-5 w-5" /> Start quest <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </motion.section>
    </motion.div>
  );
}
