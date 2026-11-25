import { Link, Navigate, Route, Routes } from "react-router-dom";
import ParticipantApp from "./participant/ParticipantApp";
import ResearcherApp from "./researcher/ResearcherApp";

function Home() {
  return (
    <main className="mx-auto flex min-h-full max-w-3xl flex-col justify-center gap-8 px-4 py-12">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700 dark:text-blue-400">Student research study</p>
        <h1 className="mt-2 text-3xl font-bold">SMIT — Spatial Memory Interference Task</h1>
        <p className="mt-3 text-slate-600 dark:text-slate-400">Choose how you are using this computer.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Link to="/participate" className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:border-blue-500 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">Take part</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Start the memory task as a participant.</p>
        </Link>
        <Link to="/researcher" className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:border-blue-500 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xl font-semibold">Researcher dashboard</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Configure, pilot, monitor, import data, analyse and generate reports.</p>
        </Link>
      </div>
    </main>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/participate" element={<ParticipantApp />} />
      <Route path="/researcher/*" element={<ResearcherApp />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
