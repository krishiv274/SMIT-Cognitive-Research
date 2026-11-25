import { useState, type FormEvent, type ReactNode } from "react";
import { Alert, Button, Field, GridIllustration, inputCls } from "../components/ui";
import type { ExperimentConfig } from "../types";

export interface StudyInfo {
  title: string;
  short_title: string;
  purpose: string;
  estimated_minutes: string;
  main_study_open: boolean;
  mode: "main" | "pilot";
  experiment_version: string | null;
  config: ExperimentConfig | null;
  settings: Record<string, string>;
}

export function Shell({ children, pilot }: { children: ReactNode; pilot?: boolean }) {
  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      {pilot && <div className="mb-4"><Alert kind="warn"><strong>PILOT MODE</strong> — data are stored as pilot data and excluded from the main analysis.</Alert></div>}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8 dark:border-slate-800 dark:bg-slate-900">{children}</div>
    </main>
  );
}

export function Welcome({ info, onNext }: { info: StudyInfo; onNext: () => void }) {
  const s = info.settings;
  return (
    <Shell pilot={info.mode === "pilot"}>
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-700 dark:text-blue-400">Student research study · {s.course_name}</p>
      <h1 className="mt-2 text-2xl font-bold leading-snug">{info.title}</h1>
      <p className="mt-4">{info.purpose}</p>
      <ul className="mt-4 list-disc space-y-1 pl-5 text-slate-700 dark:text-slate-300">
        <li>Estimated duration: <strong>{info.estimated_minutes} minutes</strong>.</li>
        <li>You will use the <strong>F</strong> and <strong>J</strong> keys. Please sit comfortably, about an arm's length from the screen.</li>
        <li>The task runs in full-screen mode. Please silence your phone and do not switch windows.</li>
        <li>You must be <strong>18 or older</strong> to take part.</li>
      </ul>
      <h2 className="mt-6 font-semibold">Privacy</h2>
      <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
        You will be identified in the data only by an automatically generated participant ID. Your email address is stored separately and never
        appears in any report. {s.data_storage_statement}
      </p>
      <div className="mt-8 flex justify-end"><Button onClick={onNext}>Continue</Button></div>
    </Shell>
  );
}

export function Consent({ info, onAccept, onDecline }: { info: StudyInfo; onAccept: () => void; onDecline: () => void }) {
  const [checked, setChecked] = useState(false);
  const s = info.settings;
  return (
    <Shell pilot={info.mode === "pilot"}>
      <h1 className="text-2xl font-bold">Information and consent</h1>
      <div className="mt-4 space-y-3 text-sm leading-relaxed text-slate-800 dark:text-slate-200">
        <p><strong>This is a student research study</strong> conducted for a {s.course_name} course at {s.university_name}, {s.department}, supervised by {s.professor_name}.</p>
        <p><strong>Ethics status:</strong> {s.ethics_statement}</p>
        <p><strong>Purpose.</strong> We are studying how people remember the positions of shapes for a few seconds while doing other brief tasks. The results will be used for a course research report.</p>
        <p><strong>What you will do.</strong> Provide your age, gender, academic course and email address; read instructions; complete 6 practice trials and 60 short trials in three blocks with breaks (about {info.estimated_minutes} minutes).</p>
        <p><strong>Voluntary participation and withdrawal.</strong> Taking part is voluntary. You may stop at any time without giving a reason and without penalty (press Esc and tell the researcher). You can ask for your data to be deleted until {s.withdrawal_deadline} by quoting your participant ID.</p>
        <p><strong>Data collected.</strong> Age, gender, academic course, email address (stored separately), your responses and reaction times, and technical information about the browser and screen needed to check timing.</p>
        <p><strong>Confidentiality.</strong> Research data are identified only by a participant ID. Only the student researchers can access your email address; it is never included in reports, figures or presentations. {s.data_storage_statement} {s.retention_statement}</p>
        <p><strong>Risks.</strong> Minimal: some people find the task mildly tiring or experience brief eye strain. The task shows rapidly appearing (but not flickering) grids; please do not take part if you have photosensitive epilepsy.</p>
        <p><strong>Contact.</strong> Researchers: {s.student_names} ({s.researcher_contact}). Supervisor: {s.professor_name} ({s.supervisor_contact}).</p>
      </div>
      <label className="mt-6 flex items-start gap-3 rounded-lg border border-slate-200 p-4 dark:border-slate-700">
        <input type="checkbox" className="mt-1 h-5 w-5" checked={checked} onChange={(e) => setChecked(e.target.checked)} aria-describedby="consent-text" />
        <span id="consent-text" className="text-sm">
          I have read and understood the information above. I am 18 years or older. I understand that participation is voluntary and that I can withdraw at any time. I agree to take part in this study.
        </span>
      </label>
      <div className="mt-6 flex flex-wrap justify-between gap-3">
        <Button variant="secondary" onClick={onDecline}>I do not wish to take part</Button>
        <Button onClick={onAccept} disabled={!checked}>I consent — continue</Button>
      </div>
    </Shell>
  );
}

export interface RegistrationValues {
  age: string;
  gender: string;
  academic_course: string;
  email: string;
}

const GENDERS = ["Female", "Male", "Non-binary", "Other", "Prefer not to answer"];

export function validateRegistration(v: RegistrationValues, pilot: boolean): Partial<Record<keyof RegistrationValues, string>> {
  const e: Partial<Record<keyof RegistrationValues, string>> = {};
  const age = Number(v.age);
  if (!pilot || v.age) {
    if (!v.age || !Number.isInteger(age)) e.age = "Please enter your age in whole years.";
    else if (age < 18) e.age = "You must be 18 or older to take part.";
    else if (age > 120) e.age = "Please check your age.";
  }
  if (!pilot && !v.gender) e.gender = "Please choose an option (you may choose 'Prefer not to answer').";
  if (!pilot && !v.academic_course.trim()) e.academic_course = "Please enter your academic course.";
  if (v.academic_course && /^[=+\-@]|[<>{}\\]/.test(v.academic_course.trim())) e.academic_course = "Please use letters, numbers and simple punctuation only.";
  if (!pilot || v.email) {
    if (!/^[^@\s<>"']{1,64}@[A-Za-z0-9.-]{1,180}\.[A-Za-z]{2,24}$/.test(v.email.trim())) e.email = "Please enter a valid email address.";
  }
  return e;
}

export function Registration({ pilot, onSubmit, busy, serverError }: { pilot: boolean; onSubmit: (v: RegistrationValues) => void; busy: boolean; serverError: string | null }) {
  const [v, setV] = useState<RegistrationValues>({ age: "", gender: "", academic_course: "", email: "" });
  const [errors, setErrors] = useState<Partial<Record<keyof RegistrationValues, string>>>({});
  const submit = (ev: FormEvent) => {
    ev.preventDefault();
    const e = validateRegistration(v, pilot);
    setErrors(e);
    if (Object.keys(e).length === 0) onSubmit(v);
  };
  const set = (k: keyof RegistrationValues) => (ev: { target: { value: string } }) => setV({ ...v, [k]: ev.target.value });
  return (
    <Shell pilot={pilot}>
      <h1 className="text-2xl font-bold">About you</h1>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">A participant ID will be generated automatically. {pilot && "(Pilot: fields are optional.)"}</p>
      <form className="mt-6 grid gap-4 sm:grid-cols-2" onSubmit={submit} noValidate>
        <Field label="Age (years)" error={errors.age}><input className={inputCls} inputMode="numeric" name="age" value={v.age} onChange={set("age")} /></Field>
        <Field label="Gender" error={errors.gender}>
          <select className={inputCls} name="gender" value={v.gender} onChange={set("gender")}>
            <option value="">Select…</option>
            {GENDERS.map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
        </Field>
        <Field label="Academic course" hint="e.g. BSc Psychology, BTech Computer Science" error={errors.academic_course}>
          <input className={inputCls} name="academic_course" maxLength={120} value={v.academic_course} onChange={set("academic_course")} />
        </Field>
        <Field label="Email address" hint="Stored separately from your task data" error={errors.email}>
          <input className={inputCls} type="email" name="email" autoComplete="email" value={v.email} onChange={set("email")} />
        </Field>
        {serverError && <div className="sm:col-span-2"><Alert kind="error">{serverError}</Alert></div>}
        <div className="flex justify-end sm:col-span-2"><Button type="submit" disabled={busy}>{busy ? "Saving…" : "Continue"}</Button></div>
      </form>
    </Shell>
  );
}

export function Instructions({ config, participantId, pilot, onStart, refreshHz }: { config: ExperimentConfig; participantId: string; pilot: boolean; onStart: () => void; refreshHz: number | null }) {
  const t = config.timing;
  const K = (s: string) => s.toUpperCase();
  const memColor = config.grid.memory_highlight_color;
  const visColor = config.grid.visual_interference_highlight_color;
  const symmetric = config.secondary_tasks.visual.probe === "symmetry";
  return (
    <Shell pilot={pilot}>
      <p className="text-sm text-slate-500">Participant ID: <span className="font-mono font-semibold">{participantId}</span></p>
      <h1 className="mt-1 text-2xl font-bold">Instructions</h1>
      <ol className="mt-5 space-y-6">
        <Step n={1} title="Look at the cross (+)">A cross appears in the middle of the screen. Keep your eyes on it — the grid is about to appear.</Step>
        <Step n={2} title={`Memorise the blue pattern (${(t.memory_stimulus_ms / 1000).toFixed(1)} s)`}>
          <p>A grid appears briefly. <strong>{config.grid.highlight_count} squares are blue.</strong> Remember <em>where</em> they are.</p>
          <div className="mt-3"><GridIllustration pattern={[0, 4, 5, 7]} color={memColor} label="Example memory pattern" /></div>
        </Step>
        <Step n={3} title={`Middle phase (${(t.interference_ms / 1000).toFixed(0)} s) — depends on the block`}>
          <ul className="list-disc space-y-2 pl-5">
            <li><strong>Hold:</strong> the screen is empty. Just keep the blue pattern in mind.</li>
            <li><strong>Equation:</strong> a sum such as <span className="font-mono">7 + 6 = 13</span> appears. Is it correct? <Key k={K(config.keys.secondary_true)} /> = True, <Key k={K(config.keys.secondary_false)} /> = False.</li>
            <li>
              <strong>{symmetric ? "Symmetry" : "Centre square"}:</strong> a different grid with <span className="font-semibold" style={{ color: visColor }}>orange</span> squares appears.{" "}
              {symmetric ? "Is the orange pattern symmetrical (the left side mirrors the right side)?" : "Is the centre square filled?"} <Key k={K(config.keys.secondary_true)} /> = Yes, <Key k={K(config.keys.secondary_false)} /> = No.
              <div className="mt-2 flex gap-6">
                <GridIllustration pattern={symmetric ? [0, 2, 4, 7] : [1, 4, 6, 8]} color={visColor} label={symmetric ? "Symmetrical → Yes" : "Centre filled → Yes"} />
                <GridIllustration pattern={symmetric ? [0, 1, 4, 7] : [0, 2, 3, 8]} color={visColor} label={symmetric ? "Not symmetrical → No" : "Centre empty → No"} />
              </div>
              <p className="mt-2 text-sm">The orange grid is <strong>not</strong> the pattern to remember. Keep remembering the blue one.</p>
            </li>
          </ul>
          <p className="mt-2 text-sm">Answer the middle task quickly and accurately. The middle phase always lasts the same time, even after you answer.</p>
        </Step>
        <Step n={4} title={`Compare (answer within ${(t.recognition_deadline_ms / 1000).toFixed(0)} s)`}>
          <p>A second blue grid appears. Is it <strong>exactly the same</strong> as the first blue pattern? <Key k={K(config.keys.same)} /> = Same, <Key k={K(config.keys.different)} /> = Different.</p>
          <p className="mt-1 text-sm">If it is different, exactly <strong>one</strong> blue square has moved to a new place. There are always {config.grid.highlight_count} blue squares.</p>
          <div className="mt-3 flex flex-wrap gap-6">
            <GridIllustration pattern={[0, 4, 5, 7]} color={memColor} label="Memory" />
            <GridIllustration pattern={[0, 4, 5, 7]} color={memColor} label={`Same → ${K(config.keys.same)}`} />
            <GridIllustration pattern={[0, 4, 5, 6]} color={memColor} label={`One square moved → ${K(config.keys.different)}`} />
          </div>
        </Step>
      </ol>
      <Alert kind="info">
        Respond <strong>as quickly and as accurately as you can</strong>. Keep your left index finger on <Key k={K(config.keys.same)} /> and your right index finger on <Key k={K(config.keys.different)} />.
        You will first do {config.trials.practice_per_condition * 3} practice trials with feedback. The main task has 3 blocks with short breaks and no feedback.
      </Alert>
      {refreshHz && <p className="mt-3 text-xs text-slate-500">Display check: about {refreshHz} Hz refresh rate detected.</p>}
      <div className="mt-6 flex justify-end"><Button onClick={onStart}>Start practice (full screen)</Button></div>
    </Shell>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: ReactNode }) {
  return (
    <li className="flex gap-4">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-700 text-sm font-bold text-white">{n}</span>
      <div><h2 className="font-semibold">{title}</h2><div className="mt-1 text-slate-800 dark:text-slate-200">{children}</div></div>
    </li>
  );
}

export function Key({ k }: { k: string }) {
  return <kbd className="rounded border border-slate-400 bg-slate-100 px-1.5 py-0.5 font-mono text-sm font-bold text-slate-900 dark:bg-slate-800 dark:text-slate-100">{k}</kbd>;
}

export function Message({ title, children, pilot }: { title: string; children: ReactNode; pilot?: boolean }) {
  return (
    <Shell pilot={pilot}>
      <h1 className="text-2xl font-bold">{title}</h1>
      <div className="mt-4 space-y-3">{children}</div>
    </Shell>
  );
}
