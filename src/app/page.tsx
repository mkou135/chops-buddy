import Link from "next/link";

const features = [
  {
    title: "Teacher Studio Hub",
    description:
      "Manage students, lessons, and assignments from a single, saxophone-focused dashboard.",
  },
  {
    title: "Guided Practice Sessions",
    description:
      "Auto-generated routines with tuner feedback help students build reliable chops between lessons.",
  },
  {
    title: "Practice Insights",
    description:
      "Review minutes practiced and session reflections to tailor upcoming lessons.",
  },
];

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-16 px-6 py-16">
      <section className="flex flex-col gap-6 text-center">
        <span className="mx-auto inline-flex items-center gap-2 rounded-full bg-brand-light px-4 py-1 text-sm font-semibold text-brand-dark">
          MVP in progress
        </span>
        <h1 className="text-4xl font-semibold tracking-tight text-slate-900 md:text-6xl">
          Coach better saxophone practice with Chops Buddy.
        </h1>
        <p className="mx-auto max-w-2xl text-lg text-slate-600">
          A teaching companion that transforms lesson assignments into guided practice plans,
          tracks time-on-task, and keeps teacher-student communication organized.
        </p>
        <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            href="#teacher-actions"
            className="inline-flex items-center justify-center rounded-full bg-brand-dark px-6 py-3 text-base font-semibold text-white shadow-sm transition hover:bg-brand"
          >
            Explore the MVP scope
          </Link>
          <Link
            href="/docs/design"
            className="inline-flex items-center justify-center rounded-full border border-brand-dark px-6 py-3 text-base font-semibold text-brand-dark transition hover:bg-brand-light"
          >
            Read the design document
          </Link>
          <Link
            href="/teacher/dashboard"
            className="inline-flex items-center justify-center rounded-full bg-slate-900 px-6 py-3 text-base font-semibold text-white shadow-sm transition hover:bg-slate-700"
          >
            View teacher workspace
          </Link>
        </div>
      </section>

      <section
        id="teacher-actions"
        className="grid grid-cols-1 gap-8 rounded-3xl bg-white p-8 shadow-lg ring-1 ring-brand-light md:grid-cols-3"
      >
        {features.map((feature) => (
          <article key={feature.title} className="flex flex-col gap-3 text-left">
            <h2 className="text-xl font-semibold text-brand-dark">{feature.title}</h2>
            <p className="text-base text-slate-600">{feature.description}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-10 rounded-3xl bg-slate-900 p-10 text-white md:grid-cols-2">
        <div className="space-y-4">
          <h2 className="text-3xl font-semibold">Why start with saxophone?</h2>
          <p className="text-base text-slate-200">
            Chops Buddy focuses on saxophonists first, allowing us to dial in tuner thresholds,
            repertoire, and pedagogy that matches the needs of single-reed players. The platform
            is built on Next.js and Supabase for rapid iteration and robust data security.
          </p>
        </div>
        <div className="space-y-3 rounded-2xl bg-slate-800 p-6">
          <h3 className="text-xl font-semibold">MVP milestones</h3>
          <ul className="space-y-2 text-sm text-slate-200">
            <li>• Teacher onboarding, student roster, and availability scheduling</li>
            <li>• Scale assignment composer feeding guided practice steps</li>
            <li>• Web-based tuner with pitch detection tuned for saxophone</li>
            <li>• Practice session summaries with minutes practiced and student questions</li>
          </ul>
        </div>
      </section>
    </main>
  );
}
