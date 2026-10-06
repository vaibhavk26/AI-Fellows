import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Flame, Loader2, Sparkles, Target, Trophy } from "lucide-react";
import { Aurora, Dropdown, ErrorNote, Logo } from "../components/ui";
import { ApiError, api, teacherSignupEnabled } from "../lib/api";
import { useAuth } from "../lib/auth";

const inputCls =
  "w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-white/30 outline-none transition focus:border-violet-brand focus:bg-white/10 focus:ring-4 focus:ring-violet-brand/20";

function Perk({ icon: Icon, title, text, delay }: { icon: typeof Flame; title: string; text: string; delay: number }) {
  return (
    <motion.div initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} transition={{ delay, duration: 0.5 }} className="glass flex items-center gap-4 rounded-2xl p-4">
      <div className="btn-primary grid h-11 w-11 shrink-0 place-items-center rounded-xl"><Icon className="h-5 w-5" /></div>
      <div>
        <p className="font-semibold">{title}</p>
        <p className="text-sm text-white/60">{text}</p>
      </div>
    </motion.div>
  );
}

export default function LoginPage() {
  const { user, signIn } = useAuth();
  const [mode, setMode] = useState<"in" | "up">("in");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "student" });
  const allowTeacher = teacherSignupEnabled();

  if (user) return <Navigate to="/" replace />;

  const set = (key: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [key]: e.target.value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setError(""); setNotice("");
    try {
      if (mode === "in") {
        await signIn(form.email, form.password);
      } else {
        const role = allowTeacher ? form.role : "student";
        await api.register({ full_name: form.name, email: form.email, password: form.password, role, class_level: role === "student" ? 10 : null });
        setNotice("Account created! Sign in to start your first quest.");
        setMode("in");
        setForm((f) => ({ ...f, password: "" }));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <Aurora />
      <section className="hidden flex-col justify-between p-12 lg:flex">
        <Logo size="lg" />
        <div className="max-w-lg space-y-8">
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="font-display text-5xl font-bold leading-tight">
            Make studying feel like <span className="text-gradient">levelling up.</span>
          </motion.h1>
          <p className="text-lg text-white/65">Curriculum-grounded practice, instant feedback, and a streak you won't want to break.</p>
          <div className="space-y-3">
            <Perk icon={Flame} title="Build daily streaks" text="Small sessions, big momentum." delay={0.2} />
            <Perk icon={Target} title="Find your weak spots" text="Topic-level insights tell you what to practise next." delay={0.35} />
            <Perk icon={Trophy} title="Earn XP & badges" text="Every question moves your level bar." delay={0.5} />
          </div>
        </div>
        <p className="text-sm text-white/40">© ExamIQ</p>
      </section>

      <section className="grid place-items-center p-5 sm:p-10">
        <motion.div initial={{ opacity: 0, y: 24, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.5 }} className="glass w-full max-w-md rounded-3xl p-7 sm:p-9">
          <div className="mb-6 lg:hidden"><Logo /></div>
          <div className="mb-6 flex rounded-2xl bg-white/5 p-1" role="tablist">
            {(["in", "up"] as const).map((m) => (
              <button key={m} role="tab" aria-selected={mode === m} onClick={() => { setMode(m); setError(""); setNotice(""); }}
                className={`relative flex-1 rounded-xl py-2.5 text-sm font-semibold transition-colors ${mode === m ? "text-white" : "text-white/50 hover:text-white/80"}`}>
                {mode === m && <motion.span layoutId="auth-tab" className="btn-primary absolute inset-0 -z-0 rounded-xl" />}
                <span className="relative">{m === "in" ? "Sign in" : "Create account"}</span>
              </button>
            ))}
          </div>

          <h2 className="font-display text-2xl font-bold">{mode === "in" ? "Welcome back 👋" : "Join the quest ✨"}</h2>
          <p className="mb-6 mt-1 text-sm text-white/55">{mode === "in" ? "Pick up right where you left off." : "Create your free account in seconds."}</p>

          <form onSubmit={submit} className="space-y-4">
            <AnimatePresence initial={false}>
              {mode === "up" && (
                <motion.div key="name" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
                  <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-white/50" htmlFor="name">Full name</label>
                  <input id="name" required maxLength={200} className={inputCls} placeholder="Asha Sharma" value={form.name} onChange={set("name")} />
                </motion.div>
              )}
            </AnimatePresence>
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-white/50" htmlFor="email">Email</label>
              <input id="email" type="email" required autoComplete="email" className={inputCls} placeholder="you@school.edu" value={form.email} onChange={set("email")} />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-white/50" htmlFor="password">Password</label>
              <input id="password" type="password" required minLength={8} autoComplete={mode === "in" ? "current-password" : "new-password"} className={inputCls} placeholder="At least 8 characters" value={form.password} onChange={set("password")} />
            </div>
            {mode === "up" && allowTeacher && (
              <div>
                <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-white/50" htmlFor="role">I am a</label>
                <Dropdown
                  id="role"
                  className={inputCls}
                  value={form.role}
                  onChange={(role) => setForm((f) => ({ ...f, role }))}
                  options={[{ value: "student", label: "Student" }, { value: "teacher", label: "Teacher" }]}
                />
              </div>
            )}
            {error && <ErrorNote message={error} />}
            {notice && <div role="status" className="rounded-2xl border border-lime-brand/40 bg-lime-brand/10 px-4 py-3 text-sm text-lime-100">{notice}</div>}
            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} disabled={busy} type="submit" className="btn-primary flex w-full items-center justify-center gap-2 rounded-2xl py-3.5 font-bold">
              {busy ? <Loader2 className="h-5 w-5 animate-spin" /> : <Sparkles className="h-5 w-5" />}
              {mode === "in" ? "Sign in" : "Create account"}
            </motion.button>
          </form>
        </motion.div>
      </section>
    </div>
  );
}
