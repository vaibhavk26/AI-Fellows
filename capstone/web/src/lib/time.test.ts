import { describe, expect, it } from "vitest";
import { formatClock, formatDuration, parseTimestamp, remainingSeconds } from "./time";

describe("time", () => {
  it("treats zone-less timestamps as UTC", () => {
    expect(parseTimestamp("2026-10-06T00:00:00").toISOString()).toBe("2026-10-06T00:00:00.000Z");
    expect(parseTimestamp("2026-10-06T08:00:00+08:00").toISOString()).toBe("2026-10-06T00:00:00.000Z");
  });

  it("counts down and never goes negative", () => {
    const start = "2026-10-06T00:00:00Z";
    const t = Date.parse(start);
    expect(remainingSeconds(start, 10, t + 60_000)).toBe(540);
    expect(remainingSeconds(start, 1, t + 120_000)).toBe(0);
  });

  it("formats clock and duration", () => {
    expect(formatClock(65)).toBe("01:05");
    expect(formatDuration("2026-10-06T00:00:00Z", "2026-10-06T00:02:05Z")).toBe("2m 05s");
    expect(formatDuration(null, "x")).toBe("N/A");
  });
});
