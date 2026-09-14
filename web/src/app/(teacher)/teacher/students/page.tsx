"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import { PageHeader } from "@/components/page-header";
import type { InstrumentFamily, Level, Student } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const LEVELS: Level[] = ["beginner", "intermediate", "advanced"];
const FAMILIES: InstrumentFamily[] = ["wind", "brass", "voice", "strings", "keyboard", "percussion"];

export default function StudentsPage() {
  const { api } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [level, setLevel] = useState<Level>("beginner");
  const [family, setFamily] = useState<InstrumentFamily>("wind");

  const load = useCallback(() => {
    api.listStudents().then(setStudents).catch((err) => setError(String(err)));
  }, [api]);
  useEffect(load, [load]);

  async function add(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.createStudent({ display_name: name, level, instrument_family: family });
      setName("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Students" description="Your roster. Open a student to assign targets and see their sessions." />
      <form onSubmit={add} className="flex flex-wrap items-end gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm">
        <label>
          Name
          <input required className="mt-1 block rounded-lg border px-2 py-1" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Level
          <select className="mt-1 block rounded-lg border px-2 py-1" value={level} onChange={(e) => setLevel(e.target.value as Level)}>
            {LEVELS.map((l) => (
              <option key={l}>{l}</option>
            ))}
          </select>
        </label>
        <label>
          Instrument family
          <select className="mt-1 block rounded-lg border px-2 py-1" value={family} onChange={(e) => setFamily(e.target.value as InstrumentFamily)}>
            {FAMILIES.map((f) => (
              <option key={f}>{f}</option>
            ))}
          </select>
        </label>
        <button type="submit" className="rounded-xl bg-brand-dark px-4 py-2 font-medium text-white">
          Add student
        </button>
      </form>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <ul className="grid gap-3">
        {students.map((s) => (
          <li key={s.id} className="rounded-2xl border border-slate-200 bg-white p-4">
            <Link href={`/teacher/student/?id=${s.id}`} className="font-semibold no-underline">
              {s.display_name}
            </Link>
            <div className="text-sm text-slate-600">
              {s.level} · {s.instrument_family}
            </div>
          </li>
        ))}
      </ul>
      {students.length === 0 && !error ? <p className="text-sm text-slate-600">No students yet.</p> : null}
    </div>
  );
}
