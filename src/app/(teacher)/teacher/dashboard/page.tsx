import { PageHeader } from "@/components/page-header";

const focusAreas = [
  {
    title: "This week",
    highlights: ["3 lessons scheduled", "2 assignments due", "1 student question awaiting reply"],
  },
  {
    title: "Studio health",
    highlights: ["Average practice time: 28 min", "New scale focus: Concert G Major", "Reminder: update spring recital info"],
  },
];

const quickActions = [
  {
    label: "Add student",
    description: "Create a profile, set skill level, and add notes from intake calls.",
  },
  {
    label: "Schedule lesson",
    description: "Pick an availability slot and attach a lesson goal for the week.",
  },
  {
    label: "Log lesson notes",
    description: "Capture takeaways while they are fresh to personalize assignments.",
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Teacher dashboard"
        description="Track your studio at a glance and jump into the next high-impact task."
      />

      <section className="grid gap-6 md:grid-cols-2">
        {focusAreas.map((item) => (
          <article key={item.title} className="space-y-3 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">{item.title}</h2>
            <ul className="space-y-2 text-sm text-slate-600">
              {item.highlights.map((highlight) => (
                <li key={highlight} className="flex items-start gap-2">
                  <span className="mt-1 inline-flex h-2 w-2 rounded-full bg-brand-dark" aria-hidden />
                  <span>{highlight}</span>
                </li>
              ))}
            </ul>
          </article>
        ))}
      </section>

      <section className="space-y-4 rounded-3xl border border-dashed border-brand-dark/40 bg-brand-light/40 p-6">
        <h2 className="text-lg font-semibold text-brand-dark">Quick actions</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {quickActions.map((action) => (
            <div key={action.label} className="space-y-2 rounded-2xl bg-white p-4 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900">{action.label}</h3>
              <p className="text-sm text-slate-600">{action.description}</p>
              <button
                type="button"
                className="inline-flex w-full items-center justify-center rounded-xl bg-brand-dark px-3 py-2 text-sm font-medium text-white transition hover:bg-brand"
              >
                Plan this next
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
