import { describe, expect, it } from "vitest";
import { band, computeBadges, computeStreak, computeXp, levelFromXp, pct, weakestTopic, weekActivity } from "./gamify";

const at = (iso: string) => ({ id: iso, submitted_at: iso, score_percentage: 50 });

describe("gamify", () => {
  it("clamps percentages and bands them like the Streamlit UI", () => {
    expect(pct({ score_percentage: "120" })).toBe(100);
    expect(pct({ score_percentage: null })).toBe(0);
    expect([band(80), band(60), band(59.9)]).toEqual(["strong", "good", "needs_practice"]);
  });

  it("computes consecutive-day streaks ending today or yesterday", () => {
    const now = new Date(2026, 9, 6, 12);
    expect(computeStreak([at("2026-10-06T08:00:00"), at("2026-10-05T08:00:00"), at("2026-10-03T08:00:00")], now)).toBe(2);
    expect(computeStreak([at("2026-10-05T08:00:00")], now)).toBe(1);
    expect(computeStreak([at("2026-10-01T08:00:00")], now)).toBe(0);
    expect(computeStreak([], now)).toBe(0);
  });

  it("levels up as XP grows", () => {
    expect(levelFromXp(0).level).toBe(1);
    expect(levelFromXp(60).level).toBe(2);
    expect(levelFromXp(30).progress).toBeCloseTo(0.5);
  });

  it("awards badges", () => {
    const badges = computeBadges([{ id: "1", score_percentage: 95 }], 0, []);
    expect(badges.find((b) => b.id === "first")?.earned).toBe(true);
    expect(badges.find((b) => b.id === "ace")?.earned).toBe(true);
    expect(badges.find((b) => b.id === "five")?.earned).toBe(false);
  });

  it("weights XP by accuracy but still rewards effort", () => {
    expect(computeXp(5, 0)).toBe(20);
    expect(computeXp(5, 100)).toBe(50);
    expect(computeXp(5, 50)).toBeGreaterThan(computeXp(5, 0));
  });

  it("finds the weakest topic and the weekly activity", () => {
    expect(weakestTopic([{ name: "A", score_percentage: 90, attempts: 1 }, { name: "B", score_percentage: 30, attempts: 2 }])?.name).toBe("B");
    expect(weakestTopic([{ name: "A", score_percentage: 95, attempts: 1 }])).toBeNull();
    const week = weekActivity([at("2026-10-06T08:00:00")], new Date(2026, 9, 6, 12));
    expect(week).toHaveLength(7);
    expect(week[6]).toMatchObject({ done: true, today: true });
    expect(week[5].done).toBe(false);
  });
});