"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";

import type { AttendanceStatus, Contact, Lesson, LessonStatus, School, Term } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const LESSON_STATUSES: LessonStatus[] = ["scheduled", "completed", "cancelled", "missed"];
const ATTENDANCE: AttendanceStatus[] = ["present", "absent", "late", "cancelled"];

/** School membership, lessons with attendance, and contacts for one student (M6). */
export function StudentCrm({ studentId, schoolId, onSchoolChange }: { studentId: string; schoolId: string | null; onSchoolChange: () => void }) {
  return (
    <div className="space-y-6">
      <SchoolPicker studentId={studentId} schoolId={schoolId} onChange={onSchoolChange} />
      <LessonsBlock studentId={studentId} schoolId={schoolId} />
      <ContactsBlock studentId={studentId} />
    </div>
  );
}

function SchoolPicker({ studentId, schoolId, onChange }: { studentId: string; schoolId: string | null; onChange: () => void }) {
  const { api } = useAuth();
  const [schools, setSchools] = useState<School[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.listSchools().then(setSchools).catch((err) => setError(String(err)));
  }, [api]);
  async function set(value: string) {
    setError(null);
    try {
      await api.updateStudent(studentId, { school_id: value || null });
      onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }
  return (
    <section className="text-sm">
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">School</h2>
      <select className="rounded-lg border px-2 py-1" value={schoolId ?? ""} onChange={(e) => void set(e.target.value)}>
        <option value="">none</option>
        {schools.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
      {error ? <p className="mt-1 text-red-700">{error}</p> : null}
    </section>
  );
}

function LessonsBlock({ studentId, schoolId }: { studentId: string; schoolId: string | null }) {
  const { api } = useAuth();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [terms, setTerms] = useState<Term[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [when, setWhen] = useState("");
  const [minutes, setMinutes] = useState(30);
  const [termId, setTermId] = useState("");

  const load = useCallback(async () => {
    try {
      setLessons(await api.studentLessons(studentId));
      setTerms(schoolId ? await api.listTerms(schoolId) : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [api, studentId, schoolId]);
  useEffect(() => {
    void load();
  }, [load]);

  async function schedule(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.createLesson(studentId, {
        scheduled_at: new Date(when).toISOString(),
        duration_minutes: minutes,
        term_id: termId || null,
      });
      setWhen("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function setStatus(id: string, status: LessonStatus) {
    try {
      await api.updateLesson(id, { status });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function setNotes(id: string, notes: string) {
    try {
      await api.updateLesson(id, { notes });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function mark(id: string, status: AttendanceStatus) {
    try {
      await api.setAttendance(id, { status, note: null });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <section className="space-y-3 text-sm">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Lessons</h2>
      <form onSubmit={schedule} className="flex flex-wrap items-end gap-3 rounded-2xl border border-slate-200 bg-white p-4">
        <label>
          When
          <input required type="datetime-local" className="mt-1 block rounded-lg border px-2 py-1" value={when} onChange={(e) => setWhen(e.target.value)} />
        </label>
        <label>
          Minutes
          <input type="number" min={10} max={180} className="mt-1 block w-20 rounded-lg border px-2 py-1" value={minutes} onChange={(e) => setMinutes(Number(e.target.value))} />
        </label>
        <label>
          Term
          <select className="mt-1 block rounded-lg border px-2 py-1" value={termId} onChange={(e) => setTermId(e.target.value)}>
            <option value="">none</option>
            {terms.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" className="rounded-xl bg-brand-dark px-4 py-2 font-medium text-white">
          Schedule
        </button>
      </form>
      {error ? <p className="text-red-700">{error}</p> : null}
      <ul className="grid gap-2">
        {lessons.map((l) => (
          <li key={l.id} className="rounded-2xl border border-slate-200 bg-white p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span>
                {new Date(l.scheduled_at).toLocaleString()} · {l.duration_minutes} min
              </span>
              <span className="flex flex-wrap gap-2">
                <select className="rounded-lg border px-2 py-1" value={l.status} onChange={(e) => void setStatus(l.id, e.target.value as LessonStatus)}>
                  {LESSON_STATUSES.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
                <select className="rounded-lg border px-2 py-1" value={l.attendance?.status ?? ""} onChange={(e) => void mark(l.id, e.target.value as AttendanceStatus)}>
                  <option value="" disabled>
                    attendance
                  </option>
                  {ATTENDANCE.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </span>
            </div>
            <textarea
              className="mt-2 w-full rounded-lg border px-2 py-1"
              rows={2}
              placeholder="Lesson notes"
              defaultValue={l.notes}
              onBlur={(e) => {
                if (e.target.value !== l.notes) void setNotes(l.id, e.target.value);
              }}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}

function ContactsBlock({ studentId }: { studentId: string }) {
  const { api } = useAuth();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [relationship, setRelationship] = useState("parent");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [primary, setPrimary] = useState(false);

  const load = useCallback(() => {
    api.listContacts(studentId).then(setContacts).catch((err) => setError(String(err)));
  }, [api, studentId]);
  useEffect(load, [load]);

  async function add(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.createContact(studentId, { name, relationship, phone: phone || null, email: email || null, is_primary: primary });
      setName("");
      setPhone("");
      setEmail("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function remove(id: string) {
    try {
      await api.deleteContact(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <section className="space-y-3 text-sm">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Contacts</h2>
      <ul className="grid gap-2">
        {contacts.map((c) => (
          <li key={c.id} className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-white p-3">
            <span>
              <span className="font-medium">{c.name}</span> <span className="text-slate-500">({c.relationship})</span>
              {c.is_primary ? <span className="ml-2 rounded bg-brand-light px-1.5 py-0.5 text-xs">primary</span> : null}
              <div className="text-xs text-slate-500">{[c.phone, c.email].filter(Boolean).join(" · ")}</div>
            </span>
            <button type="button" onClick={() => void remove(c.id)} className="text-xs text-red-700">
              Remove
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={add} className="flex flex-wrap items-end gap-3 rounded-2xl border border-slate-200 bg-white p-4">
        <label>
          Name
          <input required className="mt-1 block rounded-lg border px-2 py-1" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Relationship
          <input required className="mt-1 block w-28 rounded-lg border px-2 py-1" value={relationship} onChange={(e) => setRelationship(e.target.value)} />
        </label>
        <label>
          Phone
          <input className="mt-1 block rounded-lg border px-2 py-1" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </label>
        <label>
          Email
          <input type="email" className="mt-1 block rounded-lg border px-2 py-1" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={primary} onChange={(e) => setPrimary(e.target.checked)} /> primary
        </label>
        <button type="submit" className="rounded-xl bg-brand-dark px-4 py-2 font-medium text-white">
          Add contact
        </button>
      </form>
      {error ? <p className="text-red-700">{error}</p> : null}
    </section>
  );
}
