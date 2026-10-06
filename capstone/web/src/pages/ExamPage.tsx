import { useCallback, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import ExamRunner from "./exam/ExamRunner";
import ExamSetup, { type ActiveExam } from "./exam/ExamSetup";

interface Stored { active: ActiveExam; answers: Record<string, string>; index: number }
const KEY = "examiq.active";

function load(): Stored | null {
  try {
    const parsed = JSON.parse(sessionStorage.getItem(KEY) ?? "null") as Stored | null;
    return parsed?.active?.attempt?.status === "in_progress" ? parsed : null;
  } catch {
    return null;
  }
}

/** Active exam state survives a page refresh within the browser tab. */
export default function ExamPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [state, setState] = useState<Stored | null>(load);

  const update = useCallback((next: Stored | null) => {
    if (next) sessionStorage.setItem(KEY, JSON.stringify(next));
    else sessionStorage.removeItem(KEY);
    setState(next);
  }, []);

  if (!state) {
    return <ExamSetup autoStartId={params.get("assignment")} onAutoStarted={() => setParams({}, { replace: true })} onStart={(active) => update({ active, answers: {}, index: 0 })} />;
  }
  return (
    <ExamRunner
      active={state.active}
      answers={state.answers}
      index={state.index}
      onAnswers={(answers) => update({ ...state, answers })}
      onIndex={(index) => update({ ...state, index })}
      onSubmitted={(result) => { update(null); navigate(`/results?attempt=${result.id}&new=1`); }}
      onEnd={() => update(null)}
    />
  );
}
