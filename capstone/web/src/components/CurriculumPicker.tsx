import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Dropdown } from "./ui";

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
        <Dropdown
          className={field}
          value={subjectId}
          onChange={(value) => { setSubject(value); setChapter(""); setTopic(""); }}
          options={[
            ...(allSubjects ? [{ value: "", label: "All subjects" }] : []),
            ...(subjects.data ?? []).map((s) => ({ value: s.id, label: s.name })),
          ]}
        />
      </label>
      <label className={label}>Chapter
        <Dropdown
          className={field}
          value={chapterId}
          disabled={!subjectId || !chapters.data?.length}
          onChange={(value) => { setChapter(value); setTopic(""); }}
          options={[
            ...((allChapters || allSubjects) ? [{ value: "", label: "All chapters" }] : []),
            ...(chapters.data ?? []).map((c) => ({ value: c.id, label: c.name })),
          ]}
        />
        {noChapters && <span className="mt-1 block text-xs normal-case tracking-normal text-white/45">No chapters are available for the selected subject.</span>}
      </label>
      {showTopic && (
        <label className={label}>Topic
          <Dropdown
            className={field}
            value={topicId}
            disabled={!chapterId}
            onChange={setTopic}
            options={[
              { value: "", label: "All topics" },
              ...(topics.data ?? []).map((t) => ({ value: t.id, label: t.name })),
            ]}
          />
        </label>
      )}
    </>
  );
}

export const formField = field;
export const formLabel = label;
