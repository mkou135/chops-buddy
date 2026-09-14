"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { SessionPlanView } from "@/components/session-plan";
import type { Session, Target } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function HistoryPage() {
  const { api } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [targets, setTargets] = useState<Target[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.myHistory(), api.myTargets()])
      .then(([h, t]) => {
        setSessions(h);
        setTargets(t);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [api]);

  return (
    <div className="space-y-6">
      <PageHeader title="History" description="Every session, newest first, with what you logged." />
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      {sessions.map((s) => (
        <section key={s.id} className="space-y-2">
          <h2 className="text-sm font-semibold text-slate-700">
            {new Date(s.created_at).toLocaleString()} · {s.duration_minutes} min · {s.completed_at ? "complete" : "open"}
          </h2>
          <SessionPlanView session={s} targets={targets} />
        </section>
      ))}
      {sessions.length === 0 && !error ? <p className="text-sm text-slate-600">No sessions yet.</p> : null}
    </div>
  );
}
