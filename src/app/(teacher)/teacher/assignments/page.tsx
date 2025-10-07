import { PageHeader } from "@/components/page-header";

const assignments = [
  {
    title: "Concert G Major scale",
    student: "Alex Rivera",
    due: "Due in 3 days",
    status: "In progress",
  },
  {
    title: "Chromatic warmup - 2 octaves",
    student: "Maya Chen",
    due: "Due in 5 days",
    status: "Not started",
  },
  {
    title: "Long-tone breath builder",
    student: "Jordan Smith",
    due: "Due tomorrow",
    status: "Completed",
  },
];

const templates = [
  {
    name: "Major scale",
    description: "Select key, octave range, tempo goal, and tuner tolerance.",
  },
  {
    name: "Chromatic drill",
    description: "Customize start note, range, and subdivisions.",
  },
  {
    name: "Long tone",
    description: "Define sustain length, dynamics, and rest intervals.",
  },
];

export default function AssignmentsPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Assignments"
        description="Assign scales and drills, then monitor student progress through guided sessions."
        actions={
          <button
            type="button"
            className="rounded-xl bg-brand-dark px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand"
          >
            Create assignment
          </button>
        }
      />

      <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Active assignments</h2>
          <div className="flex flex-wrap gap-2">
            <button className="rounded-xl border border-brand-dark px-3 py-2 text-sm text-brand-dark transition hover:bg-brand-light" type="button">
              Filter by student
            </button>
            <button className="rounded-xl border border-brand-dark px-3 py-2 text-sm text-brand-dark transition hover:bg-brand-light" type="button">
              Sort by due date
            </button>
          </div>
        </div>
        <div className="grid gap-4">
          {assignments.map((assignment) => (
            <article key={assignment.title} className="flex flex-col gap-2 rounded-2xl border border-slate-100 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-base font-semibold text-slate-900">{assignment.title}</h3>
                <p className="text-sm text-slate-600">{assignment.student}</p>
              </div>
              <div className="flex flex-col items-start gap-2 text-sm text-slate-600 md:flex-row md:items-center">
                <span>{assignment.due}</span>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand-dark shadow-sm">
                  {assignment.status}
                </span>
                <button className="rounded-xl bg-brand-dark px-3 py-2 text-sm font-medium text-white transition hover:bg-brand" type="button">
                  View details
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-dashed border-brand-dark/40 bg-brand-light/40 p-6">
        <h2 className="text-lg font-semibold text-brand-dark">Assignment templates</h2>
        <p className="mt-2 text-sm text-brand-dark/80">
          Templates help standardize guided practice steps. Customize them as you learn what motivates each student.
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {templates.map((template) => (
            <article key={template.name} className="space-y-2 rounded-2xl bg-white p-4 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900">{template.name}</h3>
              <p className="text-sm text-slate-600">{template.description}</p>
              <button className="inline-flex items-center justify-center rounded-xl border border-brand-dark px-3 py-2 text-sm font-medium text-brand-dark transition hover:bg-brand-light" type="button">
                Customize template
              </button>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
