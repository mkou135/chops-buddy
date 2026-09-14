"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import type { Lesson } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export default function SchedulePage() {
  const { api } = useAuth();
  const today = new Date();
  const [from, setFrom] = useState(isoDate(today));
  const [to, setTo] = useState(isoDate(new Date(today.getTime() + 14 * 86400000)));
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .schedule(from, to)
      .then(setLessons)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, [api, from, to]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Schedule"
        description="Lessons across all your students in the chosen window."
        actions={
          <>
            <input type="date" className="rounded-lg border px-2 py-1 text-sm" value={from} onChange={(e) => setFrom(e.target.value)} />
            <span className="text-sm text-slate-500">to</span>
            <input type="date" className="rounded-lg border px-2 py-1 text-sm" value={to} onChange={(e) => setTo(e.target.value)} />
          </>
        }
      />
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <ul className="grid gap-2">
        {lessons.map((l) => (
          <li key={l.id} className="flex flex-wrap items-baseline justify-between gap-2 rounded-2xl border border-slate-200 bg-white p-3 text-sm">
            <span>
              {new Date(l.scheduled_at).toLocaleString()} · {l.duration_minutes} min ·{" "}
              <Link href={`/teacher/student/?id=${l.student_id}`}>{l.student_display_name}</Link>
            </span>
            <span className="text-slate-500">
              {l.status}
              {l.attendance ? ` · ${l.attendance.status}` : ""}
            </span>
          </li>
        ))}
      </ul>
      {lessons.length === 0 && !error ? <p className="text-sm text-slate-600">Nothing scheduled in this window.</p> : null}
    </div>
  );
}
