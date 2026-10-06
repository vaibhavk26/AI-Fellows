import { NavLink, Outlet } from "react-router-dom";
import { motion } from "framer-motion";
import { BarChart3, BookOpen, ClipboardList, Home, LogOut, PenSquare, Sparkles, Trophy, Users } from "lucide-react";
import { Aurora, Logo } from "./ui";
import { useAuth } from "../lib/auth";

const STUDENT_NAV = [
  { to: "/", label: "Home", icon: Home, end: true },
  { to: "/dashboard", label: "Progress", icon: BarChart3 },
  { to: "/exam", label: "Exam", icon: PenSquare },
  { to: "/results", label: "Results", icon: Trophy },
];

const TEACHER_NAV = [
  { to: "/", label: "Hub", icon: Home, end: true },
  { to: "/roster", label: "Roster", icon: Users },
  { to: "/assessments", label: "Assess", icon: ClipboardList },
  { to: "/questions", label: "Bank", icon: BookOpen },
  { to: "/generate", label: "Generate", icon: Sparkles },
];
export function AppShell() {
  const { user, signOut } = useAuth();
  const NAV = user?.role === "teacher" ? TEACHER_NAV : STUDENT_NAV;
  return (
    <div className="min-h-screen">
      <Aurora />
      <aside className="glass fixed inset-y-3 left-3 z-20 hidden w-64 flex-col rounded-3xl p-5 md:flex">
        <Logo />
        <nav className="mt-10 flex flex-1 flex-col gap-1.5">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition-colors ${
                  isActive ? "text-white" : "text-white/60 hover:text-white"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.span layoutId="nav-pill" className="btn-primary absolute inset-0 -z-10 rounded-2xl" transition={{ type: "spring", stiffness: 380, damping: 32 }} />
                  )}
                  <Icon className="h-5 w-5" />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="rounded-2xl bg-white/5 p-3">
          <div className="flex items-center gap-3">
            <div className="btn-primary grid h-10 w-10 place-items-center rounded-full text-sm font-bold">
              {(user?.full_name ?? "?").charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{user?.full_name}</p>
              <p className="truncate text-xs capitalize text-white/50">{user?.role}</p>
            </div>
            <button onClick={signOut} aria-label="Sign out" title="Sign out" className="rounded-xl p-2 text-white/60 transition hover:bg-white/10 hover:text-white">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <nav className="glass fixed inset-x-3 bottom-3 z-20 flex justify-around rounded-3xl p-2 md:hidden">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => `flex flex-col items-center gap-0.5 rounded-2xl px-4 py-2 text-[11px] font-semibold ${isActive ? "btn-primary text-white" : "text-white/60"}`}>
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
        <button onClick={signOut} className="flex flex-col items-center gap-0.5 rounded-2xl px-4 py-2 text-[11px] font-semibold text-white/60">
          <LogOut className="h-5 w-5" />
          Sign out
        </button>
      </nav>

      <main className="px-4 pb-28 pt-6 md:ml-72 md:px-8 md:pb-10">
        <div className="mx-auto max-w-6xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
