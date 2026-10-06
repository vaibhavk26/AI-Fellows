import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Component, Suspense, lazy, type ReactNode } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { Aurora } from "./components/ui";
import { AuthProvider, useAuth } from "./lib/auth";
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const HomePage = lazy(() => import("./pages/HomePage"));
import LoginPage from "./pages/LoginPage";
const AssessmentsPage = lazy(() => import("./pages/AssessmentsPage"));
const GeneratePage = lazy(() => import("./pages/GeneratePage"));
const QuestionBankPage = lazy(() => import("./pages/QuestionBankPage"));
const RosterPage = lazy(() => import("./pages/RosterPage"));
const TeacherHomePage = lazy(() => import("./pages/TeacherHomePage"));
const ExamPage = lazy(() => import("./pages/ExamPage"));
const ProfilePage = lazy(() => import("./pages/ProfilePage"));
const ResultsPage = lazy(() => import("./pages/ResultsPage"));

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 60_000, retry: false, refetchOnWindowFocus: false } } });

function Protected() {
  const { user, ready } = useAuth();
  if (!ready) return <Aurora />;
  if (!user) return <Navigate to="/login" replace />;
  return <AppShell />;
}

function RoleHome() {
  const { user } = useAuth();
  return user?.role === "teacher" ? <TeacherHomePage /> : <HomePage />;
}

function TeacherOnly({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  return user?.role === "teacher" ? <>{children}</> : <Navigate to="/" replace />;
}

function StudentOnly({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  return user?.role === "student" ? <>{children}</> : <Navigate to="/" replace />;
}

function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center p-6 text-center">
      <div className="glass max-w-md rounded-3xl p-10">
        <p className="font-display text-6xl font-bold text-gradient">404</p>
        <h1 className="mt-3 font-display text-2xl font-bold">This page wandered off</h1>
        <p className="mt-2 text-white/60">The page you are looking for does not exist.</p>
        <Link to="/" className="btn-primary mt-6 inline-flex rounded-2xl px-6 py-3 font-bold">Back to home</Link>
      </div>
    </div>
  );
}

class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="grid min-h-screen place-items-center p-6 text-center">
        <div className="glass max-w-md rounded-3xl p-10" role="alert">
          <h1 className="font-display text-2xl font-bold">Something went wrong</h1>
          <p className="mt-2 text-white/60">An unexpected error occurred. Reloading usually fixes it.</p>
          <button onClick={() => window.location.assign("/")} className="btn-primary mt-6 rounded-2xl px-6 py-3 font-bold">Reload</button>
        </div>
      </div>
    );
  }
}

export default function App() {
  return (
    <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<Aurora />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<Protected />}>
              <Route index element={<RoleHome />} />
              <Route path="dashboard" element={<StudentOnly><DashboardPage /></StudentOnly>} />
              <Route path="exam" element={<StudentOnly><ExamPage /></StudentOnly>} />
              <Route path="roster" element={<TeacherOnly><RosterPage /></TeacherOnly>} />
              <Route path="assessments" element={<TeacherOnly><AssessmentsPage /></TeacherOnly>} />
              <Route path="questions" element={<TeacherOnly><QuestionBankPage /></TeacherOnly>} />
              <Route path="generate" element={<TeacherOnly><GeneratePage /></TeacherOnly>} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="results" element={<StudentOnly><ResultsPage /></StudentOnly>} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
    </ErrorBoundary>
  );
}
