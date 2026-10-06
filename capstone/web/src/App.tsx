import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Suspense, lazy } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
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

export default function App() {
  return (
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
              <Route path="results" element={<StudentOnly><ResultsPage /></StudentOnly>} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
