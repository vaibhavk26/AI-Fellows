import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Loader2, Search, UserPlus } from "lucide-react";
import { ErrorNote, Skeleton } from "../components/ui";
import { api } from "../lib/api";

export default function RosterPage() {
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [search, setSearch] = useState("");
  const [notice, setNotice] = useState("");
  const roster = useQuery({ queryKey: ["roster"], queryFn: api.roster });

  const add = useMutation({
    mutationFn: () => api.addStudent(email),
    onSuccess: (s) => { setNotice(`Added ${s.full_name} to your roster.`); setEmail(""); qc.invalidateQueries({ queryKey: ["roster"] }); },
  });

  const all = roster.data ?? [];
  const needle = search.trim().toLowerCase();
  const visible = all.filter((s) => !needle || s.full_name.toLowerCase().includes(needle) || s.email.toLowerCase().includes(needle));

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-brand">Your class</p>
        <h1 className="font-display text-4xl font-bold">Student <span className="text-gradient">roster</span></h1>
        <p className="text-white/55">Add registered students and find them quickly.</p>
      </header>

      <form onSubmit={(e) => { e.preventDefault(); setNotice(""); add.mutate(); }} className="glass flex flex-col gap-3 rounded-3xl p-5 sm:flex-row">
        <label className="flex-1 text-xs font-semibold uppercase tracking-wider text-white/50">Student email
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="student@example.com" className="mt-1.5 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm normal-case tracking-normal text-white outline-none focus:border-violet-brand focus:ring-4 focus:ring-violet-brand/20" />
        </label>
        <button disabled={add.isPending} className="btn-primary flex items-center justify-center gap-2 self-end rounded-2xl px-6 py-3 text-sm font-bold">
          {add.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}Add student
        </button>
      </form>
      {notice && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} role="status" className="rounded-2xl bg-lime-brand/15 px-4 py-3 text-sm text-lime-brand">{notice}</motion.p>}
      {add.isError && <ErrorNote message={(add.error as Error).message} />}

      <section className="glass rounded-3xl p-5 sm:p-6">
        <div className="mb-4 flex items-center gap-3">
          <h2 className="font-display text-xl font-bold">Student list</h2>
          <div className="relative ml-auto w-full max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
            <input aria-label="Search students" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or email" className="w-full rounded-2xl border border-white/10 bg-white/5 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-violet-brand" />
          </div>
        </div>
        {roster.isLoading && <Skeleton className="h-32" />}
        {roster.isError && <ErrorNote message={(roster.error as Error).message} />}
        {roster.isSuccess && all.length === 0 && <p className="text-sm text-white/55">Your roster is empty. Add a registered student above to get started.</p>}
        {roster.isSuccess && all.length > 0 && visible.length === 0 && <p className="text-sm text-white/55">No students match that search.</p>}
        <ul className="grid gap-3 sm:grid-cols-2">
          {visible.map((s) => (
            <li key={s.id} className="flex items-center gap-3 rounded-2xl bg-white/[0.04] p-3">
              <span className="btn-primary grid h-10 w-10 place-items-center rounded-xl font-bold">{s.full_name.charAt(0).toUpperCase()}</span>
              <div className="min-w-0"><p className="truncate font-semibold">{s.full_name}</p><p className="truncate text-xs text-white/50">{s.email}</p></div>
            </li>
          ))}
        </ul>
        {roster.isSuccess && all.length > 0 && <p className="mt-4 text-xs text-white/40">Showing {visible.length} of {all.length} students</p>}
      </section>
    </div>
  );
}
