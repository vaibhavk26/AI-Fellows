import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import confetti from "canvas-confetti";
import { useEffect, useState } from "react";
import { ArrowRight, Clock, Flame, PlayCircle, Sparkles, Star, Swords, Target, TrendingUp } from "lucide-react";
import { CountUp, ErrorNote, ProgressRing, Skeleton } from "../components/ui";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { computeBadges, computeStreak, computeXp, encouragement, examsToday, greeting, levelFromXp, MAX_XP_PER_QUESTION, pct, weakestTopic, weekActivity } from "../lib/gamify";

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0 } };

export default function HomePage() {
  const { user } = useAuth();
  const analytics = useQuery({ queryKey: ["analytics", {}], queryFn: () => api.analytics({}) });
  const assignments = useQuery({ queryKey: ["assignments"], queryFn: api.assignments });

  const attempts = analytics.data?.attempts_detail ?? [];
  const summary = analytics.data?.summary ?? {};
  const xp = computeXp(Number(summary.questions_answered ?? 0), Number(summary.score_percentage ?? 0));
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

  const [levelUp, setLevelUp] = useState<number | null>(null);
  useEffect(() => {
    if (!user || analytics.isLoading) return;
    const key = `examiq.level.${user.id}`;
    const seen = Number(localStorage.getItem(key) ?? 0);
    if (seen && lvl.level > seen) {
      setLevelUp(lvl.level);
      confetti({ particleCount: 200, spread: 100, origin: { y: 0.3 } });
    }
    localStorage.setItem(key, String(Math.max(seen, lvl.level)));
  }, [user, analytics.isLoading, lvl.level]);

  const [newBadges, setNewBadges] = useState<string[]>([]);
  const [welcomed, setWelcomed] = useState(() => !!localStorage.getItem(`examiq.welcome.${user?.id}`));
  useEffect(() => {
    if (!user || analytics.isLoading) return;
    const key = `examiq.badges.${user.id}`;
    const earned = badges.filter((b) => b.earned).map((b) => b.id);
    const stored = localStorage.getItem(key);
    if (stored !== null) {
      const fresh = badges.filter((b) => b.earned && !stored.split(",").includes(b.id)).map((b) => `${b.emoji} ${b.label}`);
      if (fresh.length) setNewBadges(fresh);
    }
    localStorage.setItem(key, earned.join(","));
  }, [user, analytics.isLoading, badges.filter((b) => b.earned).length]);

  const week = weekActivity(attempts);
  const doneToday = examsToday(attempts);
  const weak = weakestTopic(analytics.data?.topics ?? []);
  const recent = [...attempts].sort((a, b) => String(b.submitted_at).localeCompare(String(a.submitted_at))).slice(0, 3);
  const pending = (assignments.data ?? []).filter((a) => a.status !== "completed");
  const firstName = user?.full_name.split(" ")[0] ?? "there";

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.header variants={item}>
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">{greeting()}</p>
        <h1 className="font-display text-4xl font-bold md:text-5xl">Ready to level up, <span className="text-gradient">{firstName}</span>?</h1>
      </motion.header>

      {levelUp && (
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} role="status" className="glass flex items-center justify-between rounded-3xl border border-amber-brand/40 p-5">
          <p className="font-display text-xl font-bold">?? Level up! You reached <span className="text-gradient">Level {levelUp}</span></p>
          <button onClick={() => setLevelUp(null)} className="text-sm text-white/60 hover:text-white">Dismiss</button>
        </motion.div>
      )}

      {newBadges.length > 0 && (
        <motion.div initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} role="status" className="glass flex items-center justify-between rounded-3xl border border-lime-brand/40 p-5">
          <p className="font-bold">Badge unlocked: <span className="text-lime-brand">{newBadges.join(", ")}</span></p>
          <button onClick={() => setNewBadges([])} className="text-sm text-white/60 hover:text-white">Dismiss</button>
        </motion.div>
      )}

      {!analytics.isLoading && attempts.length === 0 && !welcomed && (
        <section className="glass rounded-3xl border border-violet-brand/40 p-6" aria-label="Welcome">
          <h2 className="font-display text-xl font-bold">Welcome to ExamIQ - here's how it works</h2>
          <ol className="mt-3 grid gap-3 text-sm text-white/75 sm:grid-cols-3">
            <li className="rounded-2xl bg-white/5 p-4"><strong>1. Take a quest</strong><br />Start an assigned or practice exam.</li>
            <li className="rounded-2xl bg-white/5 p-4"><strong>2. Earn XP</strong><br />Accurate answers earn more XP and level you up.</li>
            <li className="rounded-2xl bg-white/5 p-4"><strong>3. Build a streak</strong><br />Practise daily to unlock badges.</li>
          </ol>
          <button onClick={() => { localStorage.setItem(`examiq.welcome.${user?.id}`, "1"); setWelcomed(true); }} className="mt-4 text-sm font-semibold text-cyan-brand hover:underline">Got it</button>
        </section>
      )}

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

      <div className="grid gap-5 lg:grid-cols-3">
        <motion.div variants={item} className="glass rounded-3xl p-6">
          <div className="mb-3 flex items-center gap-2"><Target className="h-5 w-5 text-cyan-brand" /><h2 className="font-display text-lg font-bold">Daily goal</h2></div>
          <p className="text-sm text-white/70">{doneToday >= 1 ? "Goal complete — you're on fire! 🔥" : "Finish 1 exam today to keep your streak alive."}</p>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-cyan-brand to-violet-brand transition-all" style={{ width: `${Math.min(100, doneToday * 100)}%` }} /></div>
          <div className="mt-5 flex justify-between" aria-label="Last 7 days">
            {week.map((d, i) => (
              <div key={i} className="flex flex-col items-center gap-1.5 text-[10px] font-semibold uppercase text-white/45">
                <span className={`grid h-8 w-8 place-items-center rounded-full ${d.done ? "bg-amber-brand/25 text-amber-brand" : "bg-white/[0.06]"} ${d.today ? "ring-2 ring-violet-brand" : ""}`}>{d.done ? <Flame className="h-4 w-4" fill="currentColor" /> : null}</span>
                {d.label}
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div variants={item} className="glass rounded-3xl p-6">
          <div className="mb-3 flex items-center gap-2"><Sparkles className="h-5 w-5 text-pink-brand" /><h2 className="font-display text-lg font-bold">Recommended for you</h2></div>
          {weak ? (
            <>
              <p className="text-sm text-white/70">Your weakest topic is <span className="font-semibold text-white">{weak.name}</span> at {Math.round(pct(weak))}%.</p>
              <Link to="/exam" className="btn-primary mt-5 flex items-center justify-center gap-2 rounded-2xl py-3 text-sm font-bold">Practise it now <ArrowRight className="h-4 w-4" /></Link>
            </>
          ) : (
            <>
              <p className="text-sm text-white/70">{attempts.length === 0 ? "Take your first practice exam to unlock personalised tips." : "No weak spots right now. Challenge yourself with a harder exam!"}</p>
              <Link to="/exam" className="btn-primary mt-5 flex items-center justify-center gap-2 rounded-2xl py-3 text-sm font-bold">{attempts.length === 0 ? "Start your first exam" : "Try a new exam"} <ArrowRight className="h-4 w-4" /></Link>
            </>
          )}
        </motion.div>

        <motion.div variants={item} className="glass rounded-3xl p-6">
          <div className="mb-3 flex items-center gap-2"><TrendingUp className="h-5 w-5 text-amber-brand" /><h2 className="font-display text-lg font-bold">Recent activity</h2></div>
          {recent.length === 0 ? <p className="text-sm text-white/60">Your results will show up here.</p> : (
            <ul className="space-y-2.5">
              {recent.map((a) => (
                <li key={a.id}><Link to={`/results?attempt=${a.id}`} className="flex items-center justify-between gap-3 rounded-xl bg-white/[0.04] px-3 py-2 text-sm transition hover:bg-white/10"><span className="truncate">{a.exam_title ?? "Exam"}</span><span className="font-bold tabular-nums">{Math.round(pct(a))}%</span></Link></li>
              ))}
            </ul>
          )}
          {recent[0] && <p className="mt-3 text-xs text-white/50">{encouragement(pct(recent[0]))}</p>}
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
                <p className="mb-5 mt-1 text-sm text-white/55">{a.question_count} questions · +{a.question_count * MAX_XP_PER_QUESTION} XP</p>
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
