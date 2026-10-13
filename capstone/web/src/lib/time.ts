/** Backend timestamps may omit the timezone; treat them as UTC (same as the Streamlit client). */
export function parseTimestamp(value: string): Date {
  const hasZone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(value);
  return new Date(hasZone ? value : `${value}Z`);
}

export function remainingSeconds(startedAt: string, limitMinutes: number, now: number = Date.now()): number {
  const elapsed = Math.floor((now - parseTimestamp(startedAt).getTime()) / 1000);
  return Math.max(0, limitMinutes * 60 - elapsed);
}

export function formatClock(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function formatDuration(startedAt: string | null | undefined, submittedAt: string | null | undefined): string {
  if (!startedAt || !submittedAt) return "N/A";
  const seconds = Math.max(0, Math.floor((parseTimestamp(submittedAt).getTime() - parseTimestamp(startedAt).getTime()) / 1000));
  return `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
}
