import type { Analytics, BankQuestion, CreateExamRequest, GenerateQuestionsRequest, GenerationResult, RosterStudent, TeacherDashboard, TeacherExam, Assignment, AttemptResult, AttemptStart, AttemptSummary, Chapter, Exam, GenerateExamRequest, Subject, Topic, User } from "./types";

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

let accessToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

function messageFrom(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => (d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : String(d))).join("; ");
    }
    if (detail && typeof detail === "object") {
      const d = detail as { message?: string; code?: string };
      return d.message || d.code || JSON.stringify(detail);
    }
  }
  return fallback;
}

async function request<T>(method: string, path: string, opts: { params?: Record<string, string | number | undefined>; json?: unknown } = {}): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`);
  for (const [key, value] of Object.entries(opts.params ?? {})) {
    if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
  }
  const headers: Record<string, string> = {};
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (opts.json !== undefined) headers["Content-Type"] = "application/json";

  let response: Response;
  try {
    response = await fetch(url, { method, headers, body: opts.json !== undefined ? JSON.stringify(opts.json) : undefined });
  } catch {
    throw new ApiError(0, `Can't reach the server at ${API_BASE_URL}. Is the backend running?`);
  }
  if (response.status === 401 && accessToken) onUnauthorized?.();
  if (!response.ok) {
    let payload: unknown = null;
    try { payload = await response.json(); } catch { /* non-JSON error body */ }
    throw new ApiError(response.status, messageFrom(payload, `Request failed (${response.status})`));
  }
  if (response.status === 204) return {} as T;
  return (await response.json()) as T;
}

interface Envelope<T> { data: T }

export const api = {
  login: (email: string, password: string) =>
    request<Envelope<{ access_token: string; user: User }>>("POST", "/api/v1/auth/login", { json: { email, password } }).then((r) => r.data),
  register: (body: { full_name: string; email: string; password: string; role: string; class_level: number | null }) =>
    request<unknown>("POST", "/api/v1/auth/register", { json: body }),
  me: () => request<Envelope<User>>("GET", "/api/v1/auth/me").then((r) => r.data),
  subjects: () => request<Envelope<Subject[]>>("GET", "/api/v1/curriculum/subjects", { params: { page_size: 100 } }).then((r) => r.data ?? []),
  chapters: (subjectId: string) =>
    request<Envelope<Chapter[]>>("GET", `/api/v1/curriculum/subjects/${subjectId}/chapters`, { params: { page_size: 100 } }).then((r) => r.data ?? []),
  topics: (chapterId: string) =>
    request<Envelope<Topic[]>>("GET", `/api/v1/curriculum/chapters/${chapterId}/topics`, { params: { page_size: 100 } }).then((r) => r.data ?? []),
  generateExam: (body: GenerateExamRequest) => request<Envelope<Exam>>("POST", "/api/v1/exams/generate", { json: body }).then((r) => r.data),
  getExam: (examId: string) => request<Envelope<Exam>>("GET", `/api/v1/exams/${examId}`).then((r) => r.data),
  teacherDashboard: () => request<Envelope<TeacherDashboard>>("GET", "/api/v1/teachers/me/dashboard").then((r) => r.data),
  roster: () => request<Envelope<RosterStudent[]>>("GET", "/api/v1/teachers/me/students").then((r) => r.data ?? []),
  addStudent: (email: string) => request<Envelope<RosterStudent>>("POST", "/api/v1/teachers/me/students", { json: { email } }).then((r) => r.data),
  teacherExams: () => request<Envelope<TeacherExam[]>>("GET", "/api/v1/exams", { params: { page_size: 100 } }).then((r) => r.data ?? []),
  createExam: (body: CreateExamRequest) => request<Envelope<Exam>>("POST", "/api/v1/exams/generate", { json: body }).then((r) => r.data),
  assignExam: (examId: string, studentIds: string[]) =>
    request<Envelope<unknown[]>>("POST", `/api/v1/exams/${examId}/assignments`, { json: { student_ids: studentIds } }).then((r) => r.data ?? []),
  questions: () => request<Envelope<BankQuestion[]>>("GET", "/api/v1/questions", { params: { page_size: 100 } }).then((r) => r.data ?? []),
  generateQuestions: (body: GenerateQuestionsRequest) =>
    request<{ data: GenerationResult; meta: { validated: number } }>("POST", "/api/v1/questions/generate", { json: body }),
  startAttempt: (examId: string) => request<Envelope<AttemptStart>>("POST", `/api/v1/exams/${examId}/attempts`).then((r) => r.data),
  submitAttempt: (attemptId: string, answers: { question_id: string; answer: string }[]) =>
    request<Envelope<AttemptResult>>("POST", `/api/v1/attempts/${attemptId}/submit`, { json: { answers } }).then((r) => r.data),
  attempts: () =>
    request<Envelope<AttemptSummary[]>>("GET", "/api/v1/students/me/attempts", { params: { status: "submitted", page_size: 20 } }).then((r) => r.data ?? []),
  attemptDetail: (attemptId: string) => request<Envelope<AttemptResult>>("GET", `/api/v1/attempts/${attemptId}`).then((r) => r.data),
  assignments: () => request<Envelope<Assignment[]>>("GET", "/api/v1/students/me/assignments").then((r) => r.data ?? []),
  analytics: (params: Record<string, string | undefined>) =>
    request<Envelope<Analytics>>("GET", "/api/v1/students/me/analytics", { params }).then((r) => r.data),
};

export function teacherSignupEnabled(): boolean {
  const configured = import.meta.env.VITE_ALLOW_TEACHER_SIGNUP;
  if (configured !== undefined) return ["1", "true", "yes", "on"].includes(String(configured).trim().toLowerCase());
  return import.meta.env.DEV;
}
