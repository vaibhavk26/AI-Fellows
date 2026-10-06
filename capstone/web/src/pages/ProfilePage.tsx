import { useQuery } from "@tanstack/react-query";
import { Flame, Mail, ShieldCheck } from "lucide-react";
import { Skeleton } from "../components/ui";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { computeBadges, computeStreak, computeXp, levelFromXp } from "../lib/gamify";

function StudentStats() {
  const { data, isLoading } = useQuery({ queryKey: ["analytics", {}], queryFn: () => api.analytics({}) });
  if (isLoading || !data) return <Skeleton className="h-48" />;
  const xp = computeXp(Number(data.summary.questions_answered ?? 0), Number(data.summary.score_percentage ?? 0));
  const lvl = levelFromXp(xp);
  const streak = computeStreak(data.attempts_detail ?? []);
  const badges = computeBadges(data.attempts_detail ?? [], streak, data.topics ?? []);
  return (
    <>
      <section className="grid gap-4 sm:grid-cols-3">
        <div className="glass rounded-3xl p-5"><p className="text-xs font-semibold uppercase tracking-wider text-white/50">Level</p><p className="mt-2 font-display text-4xl font-bold text-gradient">{lvl.level}</p></div>
        <div className="glass rounded-3xl p-5"><p className="text-xs font-semibold uppercase tracking-wider text-white/50">Total XP</p><p className="mt-2 font-display text-4xl font-bold">{xp}</p></div>
        <div className="glass rounded-3xl p-5"><p className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-white/50"><Flame className="h-3.5 w-3.5" />Streak</p><p className="mt-2 font-display text-4xl font-bold text-amber-brand">{streak} {streak === 1 ? "day" : "days"}</p></div>
      </section>
      <section className="glass rounded-3xl p-6">
        <h2 className="font-display text-xl font-bold">Badges</h2>
        <ul className="mt-4 grid gap-3 sm:grid-cols-2">
          {badges.map((b) => (
            <li key={b.id} className={`flex items-center gap-3 rounded-2xl bg-white/5 p-4 ${b.earned ? "" : "opacity-45"}`}>
              <span className="text-3xl" aria-hidden>{b.emoji}</span>
              <span><span className="block font-semibold">{b.label}{b.earned ? "" : " (locked)"}</span><span className="block text-xs text-white/55">{b.hint}</span></span>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

export default function ProfilePage() {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <div className="space-y-6">
      <header className="flex items-center gap-5">
        <div className="btn-primary grid h-20 w-20 place-items-center rounded-full font-display text-3xl font-bold">{user.full_name.charAt(0).toUpperCase()}</div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">Your profile</p>
          <h1 className="font-display text-4xl font-bold">{user.full_name}</h1>
          <p className="mt-1 flex flex-wrap items-center gap-4 text-sm text-white/60">
            <span className="flex items-center gap-1.5"><Mail className="h-4 w-4" />{user.email}</span>
            <span className="flex items-center gap-1.5 capitalize"><ShieldCheck className="h-4 w-4" />{user.role}</span>
          </p>
        </div>
      </header>
      {user.role === "student" && <StudentStats />}
    </div>
  );
}
