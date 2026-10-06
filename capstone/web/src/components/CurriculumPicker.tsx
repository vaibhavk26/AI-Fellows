import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export interface CurriculumValue { subjectId: string; chapterId: string; topicId: string; ready: boolean; noChapters: boolean }

const field = "mt-1.5 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm normal-case tracking-normal text-white outline-none transition focus:border-violet-brand focus:ring-4 focus:ring-violet-brand/20 disabled:opacity-50";
const label = "text-xs font-semibold uppercase tracking-wider text-white/50";

interface Props {
  onChange: (v: CurriculumValue) => void;
  /** Adds an "All subjects" option; chapter/topic then follow the "All" pattern. */
  allSubjects?: boolean;
  /** Adds an "All chapters" option instead of defaulting to the first chapter. */
  allChapters?: boolean;
  showTopic?: boolean;
}

/** Subject → chapter → topic cascade shared by the teacher screens. Empty string means "All". */
export function CurriculumPicker({ onChange, allSubjects, allChapters, showTopic }: Props) {
  const [subject, setSubject] = useState("");
  const [chapter, setChapter] = useState("");
  const [topic, setTopic] = useState("");

  const subjects = useQuery({ queryKey: ["subjects"], queryFn: api.subjects, staleTime: 300_000 });
  const subjectId = allSubjects ? subject : subject || subjects.data?.[0]?.id || "";
  const chapters = useQuery({ queryKey: ["chapters", subjectId], queryFn: () => api.chapters(subjectId), enabled: !!subjectId, staleTime: 300_000 });
  const validChapter = chapter && chapters.data?.some((c) => c.id === chapter);
  const chapterId = validChapter ? chapter : allChapters || allSubjects ? "" : chapters.data?.[0]?.id ?? "";
  const topics = useQuery({ queryKey: ["topics", chapterId], queryFn: () => api.topics(chapterId), enabled: !!chapterId && !!showTopic, staleTime: 300_000 });
  const topicId = topic && topics.data?.some((t) => t.id === topic) ? topic : "";
  const noChapters = !!subjectId && chapters.isSuccess && chapters.data.length === 0;

  useEffect(() => {
    onChange({ subjectId, chapterId, topicId, ready: !!subjectId && (allChapters || allSubjects || !!chapterId), noChapters });
  }, [subjectId, chapterId, topicId, noChapters, allChapters, allSubjects, onChange]);

  return (
    <>
      <label className={label}>Subject
        <select className={field} value={subjectId} onChange={(e) => { setSubject(e.target.value); setChapter(""); setTopic(""); }}>
          {allSubjects && <option value="" className="bg-ink-900">All subjects</option>}
          {(subjects.data ?? []).map((s) => <option key={s.id} value={s.id} className="bg-ink-900">{s.name}</option>)}
        </select>
      </label>
      <label className={label}>Chapter
        <select className={field} value={chapterId} disabled={!subjectId || !chapters.data?.length} onChange={(e) => { setChapter(e.target.value); setTopic(""); }}>
          {(allChapters || allSubjects) && <option value="" className="bg-ink-900">All chapters</option>}
          {(chapters.data ?? []).map((c) => <option key={c.id} value={c.id} className="bg-ink-900">{c.name}</option>)}
        </select>
        {noChapters && <span className="mt-1 block text-xs normal-case tracking-normal text-white/45">No chapters are available for the selected subject.</span>}
      </label>
      {showTopic && (
        <label className={label}>Topic
          <select className={field} value={topicId} disabled={!chapterId} onChange={(e) => setTopic(e.target.value)}>
            <option value="" className="bg-ink-900">All topics</option>
            {(topics.data ?? []).map((t) => <option key={t.id} value={t.id} className="bg-ink-900">{t.name}</option>)}
          </select>
        </label>
      )}
    </>
  );
}

export const formField = field;
export const formLabel = label;
