"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState, type FormEvent } from "react";

import { PageHeader } from "@/components/page-header";
import { SessionPlanView } from "@/components/session-plan";
import type { Session, StudentDetail, TargetKind } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

// Query-string id rather than a dynamic segment: static export needs no generateStaticParams.
export default function StudentDetailPage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
      <StudentDetailInner />
    </Suspense>
  );
}

function StudentDetailInner() {
  const id = useSearchParams().get("id") ?? "";
  const { api } = useAuth();
  const [student, setStudent] = useState<StudentDetail | null>(null);
  const [history, setHistory] = useState<Session[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [kind, setKind] = useState<TargetKind>("repertoire");
  const [title, setTitle] = useState("");
  const [tempo, setTempo] = useState(100);
  const [units, setUnits] = useState("b1, b2, b3, b4");
  const [startTempo, setStartTempo] = useState("");
  const [threshold, setThreshold] = useState("");

  const load = useCallback(() => {
    if (!id) return;
    Promise.all([api.getStudent(id), api.studentHistory(id)])
      .then(([s, h]) => {
        setStudent(s);
        setHistory(h);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [api, id]);
  useEffect(load, [load]);

  async function assign(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.assignTarget(id, {
        kind,
        title,
        target_tempo: tempo,
        units: units.split(",").map((u) => u.trim()).filter(Boolean),
        start_tempo: startTempo ? Number(startTempo) : null,
        threshold_override: threshold ? Number(threshold) : null,
      });
      setTitle("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function remove(targetId: string) {
    setError(null);
    try {
      await api.deactivateTarget(targetId);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  if (!id) return <p className="text-sm text-red-700">No student id in the URL.</p>;
  return (
    <div className="space-y-6">
      <PageHeader title={student?.display_name ?? "Student"} description={student ? `${student.level} · ${student.instrument_family}` : ""} />
      {error ? <p className="text-sm text-red-700">{error}</p> : null}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Assigned targets</h2>
        <ul className="grid gap-2">
          {student?.targets.map((t) => (
            <li key={t.id} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-3 text-sm">
              <div>
                <span className="font-medium">{t.title}</span> <span className="text-slate-500">({t.kind}, target {t.target_tempo} BPM)</span>
                <div className="text-xs text-slate-500">
                  {t.state.mode} at {t.state.tempo} BPM · units {t.units.join(" ")}
                </div>
              </div>
              <button type="button" onClick={() => void remove(t.id)} className="text-xs text-red-700">
                Remove
              </button>
            </li>
          ))}
        </ul>
        <form onSubmit={assign} className="grid grid-cols-2 gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm md:grid-cols-6">
          <label>
            Kind
            <select className="mt-1 w-full rounded-lg border px-2 py-1" value={kind} onChange={(e) => setKind(e.target.value as TargetKind)}>
              <option value="scale">scale</option>
              <option value="technique">technique</option>
              <option value="repertoire">repertoire</option>
            </select>
          </label>
          <label className="col-span-2">
            Title
            <input required className="mt-1 w-full rounded-lg border px-2 py-1" value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label>
            Target BPM
            <input type="number" min={20} max={300} className="mt-1 w-full rounded-lg border px-2 py-1" value={tempo} onChange={(e) => setTempo(Number(e.target.value))} />
          </label>
          <label>
            Start BPM
            <input type="number" min={20} max={300} placeholder="auto" className="mt-1 w-full rounded-lg border px-2 py-1" value={startTempo} onChange={(e) => setStartTempo(e.target.value)} />
          </label>
          <label>
            Threshold
            <input type="number" min={3} max={10} placeholder="by level" className="mt-1 w-full rounded-lg border px-2 py-1" value={threshold} onChange={(e) => setThreshold(e.target.value)} />
          </label>
          <label className="col-span-full">
            Units, comma separated. A triplet or ornament is one unit.
            <input className="mt-1 w-full rounded-lg border px-2 py-1" value={units} onChange={(e) => setUnits(e.target.value)} />
          </label>
          <button type="submit" className="w-fit rounded-xl bg-brand-dark px-4 py-2 font-medium text-white">
            Assign
          </button>
        </form>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Sessions</h2>
        {history.map((s) => (
          <div key={s.id} className="space-y-2">
            <h3 className="text-sm text-slate-700">
              {new Date(s.created_at).toLocaleString()} · {s.duration_minutes} min · {s.source} · {s.completed_at ? "complete" : "open"}
              {s.llm_report?.violations.length ? ` · validator: ${s.llm_report.violations.join(", ")}` : ""}
            </h3>
            <SessionPlanView session={s} targets={student?.targets ?? []} />
          </div>
        ))}
        {history.length === 0 ? <p className="text-sm text-slate-600">No sessions yet.</p> : null}
      </section>
    </div>
  );
}
