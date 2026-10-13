import type { AttemptDetail, ScoreRow } from "./types";

export const pct = (row: { score_percentage?: number | string | null }): number => {
  const value = Number(row.score_percentage ?? 0);
  return Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : 0;
};

export type Band = "strong" | "good" | "needs_practice";
export const band = (score: number): Band => (score >= 80 ? "strong" : score >= 60 ? "good" : "needs_practice");

export const BAND_COLOR: Record<Band, string> = {
  strong: "#a3ff6b",
  good: "#ffc247",
  needs_practice: "#ff6b8b",
};
export const BAND_LABEL: Record<Band, string> = {
  strong: "Strong",
  good: "Developing",
  needs_practice: "Needs practice",
};

export const MAX_XP_PER_QUESTION = 10;

// XP is derived client-side from existing analytics. Effort earns a base, accuracy earns the rest.
export function computeXp(questionsAnswered: number, scorePercentage: number): number {
  const accuracy = Math.max(0, Math.min(100, scorePercentage)) / 100;
  return Math.max(0, Math.round(questionsAnswered * (4 + 6 * accuracy)));
}
export function levelFromXp(xp: number) {
  const level = Math.floor(Math.sqrt(xp / 60)) + 1;
  const floor = 60 * (level - 1) ** 2;
  const next = 60 * level ** 2;
  return { level, floor, next, progress: (xp - floor) / (next - floor) };
}

const dayKey = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;

/** Consecutive days with a submitted exam, ending today or yesterday. */
export function computeStreak(attempts: AttemptDetail[], now: Date = new Date()): number {
  const days = new Set(
    attempts.filter((a) => a.submitted_at).map((a) => dayKey(new Date(a.submitted_at as string))),
  );
  const cursor = new Date(now);
  if (!days.has(dayKey(cursor))) cursor.setDate(cursor.getDate() - 1);
  let streak = 0;
  while (days.has(dayKey(cursor))) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}

export interface Badge { id: string; label: string; hint: string; emoji: string; earned: boolean }

export function computeBadges(attempts: AttemptDetail[], streak: number, topics: ScoreRow[]): Badge[] {
  const best = attempts.reduce((max, a) => Math.max(max, pct(a)), 0);
  return [
    { id: "first", label: "First Steps", hint: "Submit your first exam", emoji: "🚀", earned: attempts.length >= 1 },
    { id: "five", label: "On a Roll", hint: "Submit 5 exams", emoji: "🔥", earned: attempts.length >= 5 },
    { id: "ace", label: "Ace", hint: "Score 90%+ on an exam", emoji: "🏆", earned: best >= 90 },
    { id: "streak3", label: "3-Day Streak", hint: "Practice 3 days in a row", emoji: "⚡", earned: streak >= 3 },
    { id: "master", label: "Topic Master", hint: "Reach 80%+ in 3 topics", emoji: "🧠", earned: topics.filter((t) => pct(t) >= 80).length >= 3 },
  ];
}

export function greeting(now: Date = new Date()): string {
  const h = now.getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

export interface WeekDay { label: string; done: boolean; today: boolean }

/** The last seven days (oldest first) with whether an exam was submitted on each. */
export function weekActivity(attempts: AttemptDetail[], now: Date = new Date()): WeekDay[] {
  const days = new Set(attempts.filter((a) => a.submitted_at).map((a) => dayKey(new Date(a.submitted_at as string))));
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(now);
    d.setDate(d.getDate() - (6 - i));
    return { label: d.toLocaleDateString("en", { weekday: "narrow" }), done: days.has(dayKey(d)), today: i === 6 };
  });
}

export const examsToday = (attempts: AttemptDetail[], now: Date = new Date()): number =>
  attempts.filter((a) => a.submitted_at && dayKey(new Date(a.submitted_at)) === dayKey(now)).length;

/** The attempted topic with the lowest score, if it is not already strong. */
export function weakestTopic(topics: ScoreRow[]): ScoreRow | null {
  const tried = topics.filter((t) => Number(t.attempts ?? 1) > 0 && t.score_percentage != null);
  if (tried.length === 0) return null;
  const lowest = tried.reduce((m, t) => (pct(t) < pct(m) ? t : m));
  return pct(lowest) < 80 ? lowest : null;
}

export function encouragement(score: number): string {
  return score >= 90 ? "Outstanding! Keep that momentum going." : score >= 70 ? "Great work — a little more and you're a master." : score >= 40 ? "Good effort. Review your misses and go again." : "Every expert started here. Try a short practice round!";
}