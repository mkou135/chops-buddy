"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { SessionPlanView } from "@/components/session-plan";
import type { Session, Target } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function StudentPage() {
  const { api } = useAuth();
  const [targets, setTargets] = useState<Target[]>([]);
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [t, history] = await Promise.all([api.myTargets(), api.myHistory()]);
      setTargets(t);
      const open = history.find((s) => !s.completed_at) ?? null;
      setSession(open);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  async function start(minutes: 10 | 20 | 30) {
    setBusy(true);
    setError(null);
    try {
      setSession(await api.createSession(minutes));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={session ? "Your session" : "Start a session"}
        description={
          session
            ? `${session.duration_minutes} minutes · planned by ${session.source === "llm" ? "the model, checked by the engine" : "the engine"}`
            : "Pick a length. The engine builds the session from your teacher's assignments and what you logged last time."
        }
        actions={
          session ? null : (
            <>
              {([10, 20, 30] as const).map((m) => (
                <button key={m} disabled={busy || targets.length === 0} type="button" onClick={() => void start(m)} className="rounded-xl bg-brand-dark px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
                  {m} min
                </button>
              ))}
            </>
          )
        }
      />
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      {targets.length === 0 && !error ? <p className="text-sm text-slate-600">Nothing assigned yet. Ask your teacher.</p> : null}
      {session?.llm_report?.coaching_note ? <p className="rounded-2xl bg-brand-light p-4 text-sm">{session.llm_report.coaching_note}</p> : null}
      {session ? (
        <SessionPlanView
          session={session}
          targets={targets}
          onLog={async (body) => {
            const entry = await api.submitLog(body);
            await load();
            return entry;
          }}
        />
      ) : null}
      {session?.completed_at ? (
        <button type="button" onClick={() => setSession(null)} className="rounded-xl border border-brand-dark px-4 py-2 text-sm font-medium text-brand-dark">
          Session complete. Start another
        </button>
      ) : null}
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Assigned</h2>
        <ul className="grid gap-2 md:grid-cols-2">
          {targets.map((t) => (
            <li key={t.id} className="rounded-2xl border border-slate-200 bg-white p-3 text-sm">
              <span className="font-medium">{t.title}</span> <span className="text-slate-500">({t.kind})</span>
              <div className="text-xs text-slate-500">
                {t.state.mode} · {t.state.tempo} of {t.target_tempo} BPM
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
