"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";

import { PageHeader } from "@/components/page-header";
import type { School, Term } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function SchoolsPage() {
  const { api } = useAuth();
  const [schools, setSchools] = useState<School[]>([]);
  const [terms, setTerms] = useState<Record<string, Term[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [suburb, setSuburb] = useState("");
  const [joinId, setJoinId] = useState("");

  const load = useCallback(async () => {
    try {
      const list = await api.listSchools();
      setSchools(list);
      const entries = await Promise.all(list.map(async (s) => [s.id, await api.listTerms(s.id)] as const));
      setTerms(Object.fromEntries(entries));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [api]);
  useEffect(() => {
    void load();
  }, [load]);

  async function create(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.createSchool({ name, suburb: suburb || null });
      setName("");
      setSuburb("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function join(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.joinSchool(joinId.trim());
      setJoinId("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Schools" description="Every school you teach at. Membership lets you see that school's roster; your own students are still yours alone." />
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <div className="grid gap-4 md:grid-cols-2">
        <form onSubmit={create} className="flex flex-wrap items-end gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm">
          <label>
            Name
            <input required className="mt-1 block rounded-lg border px-2 py-1" value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label>
            Suburb
            <input className="mt-1 block rounded-lg border px-2 py-1" value={suburb} onChange={(e) => setSuburb(e.target.value)} />
          </label>
          <button type="submit" className="rounded-xl bg-brand-dark px-4 py-2 font-medium text-white">
            Add school
          </button>
        </form>
        <form onSubmit={join} className="flex flex-wrap items-end gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm">
          <label className="flex-1">
            Join an existing school by id
            <input required className="mt-1 block w-full rounded-lg border px-2 py-1 font-mono text-xs" value={joinId} onChange={(e) => setJoinId(e.target.value)} />
          </label>
          <button type="submit" className="rounded-xl border border-brand-dark px-4 py-2 font-medium text-brand-dark">
            Join
          </button>
        </form>
      </div>
      <ul className="grid gap-4">
        {schools.map((s) => (
          <li key={s.id} className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex items-baseline justify-between gap-3">
              <h2 className="font-semibold">
                {s.name} {s.suburb ? <span className="font-normal text-slate-500">· {s.suburb}</span> : null}
              </h2>
              <code className="text-xs text-slate-400">{s.id}</code>
            </div>
            <TermsBlock schoolId={s.id} terms={terms[s.id] ?? []} onChange={load} />
          </li>
        ))}
      </ul>
      {schools.length === 0 && !error ? <p className="text-sm text-slate-600">No schools yet.</p> : null}
    </div>
  );
}

function TermsBlock({ schoolId, terms, onChange }: { schoolId: string; terms: Term[]; onChange: () => Promise<void> }) {
  const { api } = useAuth();
  const [name, setName] = useState("");
  const [starts, setStarts] = useState("");
  const [ends, setEnds] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function add(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.createTerm(schoolId, { name, starts_on: starts, ends_on: ends });
      setName("");
      await onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="mt-3 text-sm">
      <ul className="mb-2 flex flex-wrap gap-2">
        {terms.map((t) => (
          <li key={t.id} className="rounded-lg bg-brand-light px-2 py-1">
            {t.name}: {t.starts_on} → {t.ends_on}
          </li>
        ))}
        {terms.length === 0 ? <li className="text-slate-500">No terms yet.</li> : null}
      </ul>
      <form onSubmit={add} className="flex flex-wrap items-end gap-2">
        <label>
          Term name
          <input required className="mt-1 block rounded-lg border px-2 py-1" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Starts
          <input required type="date" className="mt-1 block rounded-lg border px-2 py-1" value={starts} onChange={(e) => setStarts(e.target.value)} />
        </label>
        <label>
          Ends
          <input required type="date" className="mt-1 block rounded-lg border px-2 py-1" value={ends} onChange={(e) => setEnds(e.target.value)} />
        </label>
        <button type="submit" className="rounded-xl border border-brand-dark px-3 py-1.5 font-medium text-brand-dark">
          Add term
        </button>
      </form>
      {error ? <p className="mt-1 text-red-700">{error}</p> : null}
    </div>
  );
}
