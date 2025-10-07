import Link from "next/link";

import { PageHeader } from "@/components/page-header";

const students = [
  {
    id: "1",
    name: "Alex Rivera",
    level: "Intermediate",
    focus: "Tone and intonation",
    nextLesson: "Tue, 4:30 PM",
  },
  {
    id: "2",
    name: "Maya Chen",
    level: "Beginner",
    focus: "First octave finger transitions",
    nextLesson: "Wed, 5:15 PM",
  },
  {
    id: "3",
    name: "Jordan Smith",
    level: "Advanced",
    focus: "Altissimo warmups",
    nextLesson: "Thu, 6:00 PM",
  },
];

export default function StudentsPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Students"
        description="Keep roster details current to tailor assignments and track lesson history."
        actions={
          <button className="rounded-xl bg-brand-dark px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand" type="button">
            Add new student
          </button>
        }
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <p className="text-sm text-slate-600">
            Track lesson notes, assignments, and practice expectations for each player.
          </p>
          <button type="button" className="rounded-xl border border-brand-dark px-4 py-2 text-sm font-medium text-brand-dark transition hover:bg-brand-light">
            Import roster
          </button>
        </div>

        <div className="grid gap-4">
          {students.map((student) => (
            <article
              key={student.id}
              className="flex flex-col gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between"
            >
              <div>
                <h2 className="text-base font-semibold text-slate-900">{student.name}</h2>
                <p className="text-sm text-slate-600">
                  {student.level} · Focus: {student.focus}
                </p>
              </div>
              <div className="flex flex-col items-start gap-2 text-sm text-slate-500 md:flex-row md:items-center">
                <span>Next lesson: {student.nextLesson}</span>
                <Link
                  href={`/teacher/students/${student.id}`}
                  className="inline-flex items-center rounded-xl bg-white px-3 py-2 text-sm font-medium text-brand-dark shadow-sm transition hover:bg-brand-light"
                >
                  Open profile
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
