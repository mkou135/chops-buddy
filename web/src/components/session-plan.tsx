"use client";

import { useState, type FormEvent } from "react";

import type { LogCreate, LogEntry, Session, Target } from "@/lib/api";
import { fragmentLabel } from "@/lib/api";

type Props = {
  session: Session;
  targets: Target[];
  onLog?: (body: LogCreate) => Promise<LogEntry>;
};

/** A session's segments in order, with a log form under each unlogged prescription. */
export function SessionPlanView({ session, targets, onLog }: Props) {
  const logged = new Map(session.logs.map((l) => [l.prescription_id, l]));
  const byId = new Map(targets.map((t) => [t.id, t]));
  return (
    <ol className="space-y-4">
      {session.plan.segments.map((seg, i) => {
        const target = seg.target_id ? byId.get(seg.target_id) : undefined;
        const p = seg.prescription;
        const entry = p ? logged.get(p.id) : undefined;
        return (
          <li key={i} className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex items-baseline justify-between gap-3">
              <h3 className="font-semibold">
                {seg.kind === "long_tones" ? "Long tones" : target?.title ?? seg.kind}
              </h3>
              <span className="text-sm text-slate-500">{seg.minutes} min</span>
            </div>
            <p className="mt-1 text-sm text-slate-700">{seg.instruction}</p>
            {p && target ? (
              <p className="mt-1 text-xs text-slate-500">
                {p.mode} · {fragmentLabel(target.units, p.fragment)} · {p.tempo} BPM · {p.threshold} in a row
              </p>
            ) : null}
            {p && entry ? (
              <p className="mt-2 text-xs text-emerald-700">
                Logged: {entry.best_consecutive} in a row at {entry.tempo_used} BPM, felt {entry.felt_difficulty}/5. Next: {entry.state_after.mode} at {entry.state_after.tempo} BPM.
              </p>
            ) : null}
            {p && target && !entry && onLog ? <LogForm prescriptionId={p.id} tempo={p.tempo} units={target.units} fragment={p.fragment} onLog={onLog} /> : null}
          </li>
        );
      })}
      {session.plan.deferred.length ? (
        <li className="text-xs text-slate-500">Deferred this session: {session.plan.deferred.map((id) => byId.get(id)?.title ?? id).join(", ")}</li>
      ) : null}
    </ol>
  );
}

function LogForm({
  prescriptionId,
  tempo,
  units,
  fragment,
  onLog,
}: {
  prescriptionId: string;
  tempo: number;
  units: string[];
  fragment: [number, number];
  onLog: (body: LogCreate) => Promise<LogEntry>;
}) {
  const [tempoUsed, setTempoUsed] = useState(tempo);
  const [best, setBest] = useState(0);
  const [breakUnit, setBreakUnit] = useState<string>("");
  const [difficulty, setDifficulty] = useState(3);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [start, end] = fragment;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await onLog({
        prescription_id: prescriptionId,
        tempo_used: tempoUsed,
        best_consecutive: best,
        break_unit: breakUnit === "" ? null : Number(breakUnit),
        felt_difficulty: difficulty,
        free_text: text.trim() || null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="mt-3 grid grid-cols-2 gap-3 text-sm md:grid-cols-5">
      <label>
        Tempo used
        <input type="number" min={20} max={300} className="mt-1 w-full rounded-lg border px-2 py-1" value={tempoUsed} onChange={(e) => setTempoUsed(Number(e.target.value))} />
      </label>
      <label>
        Best in a row
        <input type="number" min={0} max={50} className="mt-1 w-full rounded-lg border px-2 py-1" value={best} onChange={(e) => setBest(Number(e.target.value))} />
      </label>
      <label>
        Where it broke
        <select className="mt-1 w-full rounded-lg border px-2 py-1" value={breakUnit} onChange={(e) => setBreakUnit(e.target.value)}>
          <option value="">nowhere</option>
          {units.slice(start, end).map((u, i) => (
            <option key={u} value={start + i}>
              {u}
            </option>
          ))}
        </select>
      </label>
      <label>
        Felt (1 easy – 5 hard)
        <input type="number" min={1} max={5} className="mt-1 w-full rounded-lg border px-2 py-1" value={difficulty} onChange={(e) => setDifficulty(Number(e.target.value))} />
      </label>
      <label className="col-span-2 md:col-span-1">
        Notes
        <input className="mt-1 w-full rounded-lg border px-2 py-1" maxLength={500} value={text} onChange={(e) => setText(e.target.value)} />
      </label>
      {error ? <p className="col-span-full text-red-700">{error}</p> : null}
      <button disabled={busy} type="submit" className="col-span-full w-fit rounded-xl bg-brand-dark px-3 py-1.5 font-medium text-white disabled:opacity-50">
        {busy ? "Saving…" : "Log it"}
      </button>
    </form>
  );
}
