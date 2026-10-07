export type Role = "student" | "teacher";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  class_level: number | null;
}

export interface Subject { id: string; name: string }
export interface Chapter { id: string; name: string }

export interface Assignment {
  id: string;
  exam_id: string;
  exam_title: string;
  question_count: number;
  time_limit_minutes: number | null;
  status: string;
  assigned_at: string;
}

export interface ScoreRow {
  id?: string;
  name?: string;
  subject_name?: string;
  chapter_name?: string;
  attempts?: number;
  score_percentage?: number | string | null;
  status?: string;
}

export interface AttemptDetail {
  id: string;
  exam_title?: string;
  submitted_at?: string;
  score?: number | string;
  max_score?: number | string;
  score_percentage?: number | string | null;
  subjects?: string[];
  chapters?: string[];
}

export interface Topic { id: string; name: string }

export interface McqOption { key: string; text: string }

export interface ExamQuestion {
  id: string;
  sequence_no: number;
  question: {
    id: string;
    topic_id: string | null;
    question_type: "mcq" | "numerical";
    difficulty: string;
    marks: number;
    question_text: string;
    options: McqOption[] | null;
  };
}

export interface Exam {
  id: string;
  title: string;
  question_count: number;
  time_limit_minutes: number;
  questions: ExamQuestion[];
}

export interface AttemptStart { id: string; exam_id: string; status: string; started_at: string }

export interface AttemptSummary {
  id: string;
  exam_id: string;
  status: string;
  started_at: string | null;
  submitted_at: string | null;
  score: number | string | null;
  max_score: number | string | null;
  percentage: number | string | null;
}

export interface AnswerResult {
  question_id: string;
  question_text: string;
  question_type: string;
  options: McqOption[] | null;
  topic_name: string | null;
  submitted_answer: string | null;
  is_correct: boolean;
  score_awarded: number | string;
  max_score: number | string;
  correct_answer: string;
  explanation: string | null;
}

export interface AttemptResult {
  id: string;
  exam_id: string;
  status: string;
  score: number | string;
  max_score: number | string;
  percentage: number | string;
  submitted_at: string;
  answers: AnswerResult[];
  weak_topics: { topic_name: string | null; score_percentage: number | string }[];
}

export interface GenerateExamRequest {
  subject_id: string;
  chapter_id: string | null;
  topic_id: string | null;
  difficulty: "easy" | "medium" | "hard";
  question_types: ("mcq" | "numerical")[];
  question_count: number;
  time_limit_minutes: number;
}

export interface Analytics {
  summary: {
    attempts?: number;
    questions_answered?: number;
    score?: number | string;
    max_score?: number | string;
    score_percentage?: number | string | null;
  };
  subjects: ScoreRow[];
  chapters: ScoreRow[];
  topics: ScoreRow[];
  attempts_detail: AttemptDetail[];
}

export interface RosterStudent { id: string; full_name: string; email: string }
export interface TeacherExam { id: string; title: string }
export interface BankQuestion {
  id: string;
  subject_id: string;
  chapter_id: string;
  topic_id: string | null;
  difficulty: string;
  question_type: string;
  status: string;
  marks: number;
  question_text: string;
  options: McqOption[] | null;
  expected_answer: string;
  explanation: string;
  learning_objective: string;
}
export interface TeacherDashboard {
  questions: { validated: number; generated: number; rejected: number };
  assignments: { total: number; started: number; completed: number; average_score_percentage: number | string | null };
  exam_performance: { exam_id?: string; title: string; assigned: number; started: number; completed: number; average_score_percentage: number | string | null }[];
}
export interface CreateExamRequest {
  title: string;
  subject_id: string;
  chapter_id: string | null;
  difficulty: "easy" | "medium" | "hard";
  question_types: ("mcq" | "numerical")[];
  question_count: number;
  time_limit_minutes: number;
}
export interface GenerateQuestionsRequest {
  subject_id: string;
  chapter_id: string;
  topic_id: string | null;
  difficulty: "easy" | "medium" | "hard";
  question_type: "mcq" | "numerical";
  marks: number;
  number_of_questions: number;
  bloom_level: "remember" | "understand" | "apply" | "analyze";
}
export interface GeneratedQuestion { question_text: string; status: string; difficulty: string; marks: number; rejection_reasons?: string[] | null }
export interface GenerationResult { questions: GeneratedQuestion[]; validated: number }
