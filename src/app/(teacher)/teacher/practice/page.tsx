import { PageHeader } from "@/components/page-header";

const sessions = [
  {
    student: "Alex Rivera",
    assignment: "Concert G Major scale",
    duration: "18 min",
    completedAt: "Yesterday",
  },
  {
    student: "Maya Chen",
    assignment: "Chromatic warmup",
    duration: "12 min",
    completedAt: "2 days ago",
  },
  {
    student: "Jordan Smith",
    assignment: "Long-tone breath builder",
    duration: "20 min",
    completedAt: "3 days ago",
  },
];

const practiceInsights = [
  {
    label: "Average minutes / session",
    value: "16",
    trend: "+4 vs. last week",
  },
  {
    label: "Assignments completed",
    value: "5",
    trend: "2 in review",
  },
  {
    label: "Questions raised",
    value: "3",
    trend: "Reply to keep momentum",
  },
];

export default function PracticePage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Practice log"
        description="Guided session summaries update automatically from the student practice experience."
        actions={
          <button
            type="button"
            className="rounded-xl border border-brand-dark px-4 py-2 text-sm font-medium text-brand-dark transition hover:bg-brand-light"
          >
            Export CSV
          </button>
        }
      />

      <section className="grid gap-4 md:grid-cols-3">
        {practiceInsights.map((insight) => (
          <article key={insight.label} className="space-y-1 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm text-slate-500">{insight.label}</p>
            <p className="text-3xl font-semibold text-slate-900">{insight.value}</p>
            <p className="text-xs uppercase tracking-wide text-brand-dark">{insight.trend}</p>
          </article>
        ))}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Recent guided sessions</h2>
          <div className="flex flex-wrap gap-2 text-sm">
            <button className="rounded-xl border border-brand-dark px-3 py-2 text-brand-dark transition hover:bg-brand-light" type="button">
              Filter by assignment
            </button>
            <button className="rounded-xl border border-brand-dark px-3 py-2 text-brand-dark transition hover:bg-brand-light" type="button">
              Date range
            </button>
          </div>
        </div>
        <div className="grid gap-3">
          {sessions.map((session) => (
            <article key={`${session.student}-${session.assignment}`} className="flex flex-col gap-2 rounded-2xl border border-slate-100 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-base font-semibold text-slate-900">{session.assignment}</h3>
                <p className="text-sm text-slate-600">{session.student}</p>
              </div>
              <div className="flex flex-col items-start gap-2 text-sm text-slate-600 md:flex-row md:items-center">
                <span>{session.duration}</span>
                <span>{session.completedAt}</span>
                <button className="rounded-xl bg-brand-dark px-3 py-2 text-sm font-medium text-white transition hover:bg-brand" type="button">
                  View summary
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
