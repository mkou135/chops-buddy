import { notFound } from "next/navigation";

import { PageHeader } from "@/components/page-header";

const mockStudents = {
  "1": {
    name: "Alex Rivera",
    level: "Intermediate",
    goals: ["Strengthen tone across the break", "Expand scale fluency to three sharps"],
  },
  "2": {
    name: "Maya Chen",
    level: "Beginner",
    goals: ["Solidify first five notes", "Introduce articulation patterns"],
  },
  "3": {
    name: "Jordan Smith",
    level: "Advanced",
    goals: ["Develop altissimo flexibility", "Prepare for juries"],
  },
} satisfies Record<string, { name: string; level: string; goals: string[] }>;

type StudentProfilePageProps = {
  params: {
    id: string;
  };
};

export default function StudentProfilePage({ params }: StudentProfilePageProps) {
  const student = mockStudents[params.id];

  if (!student) {
    notFound();
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title={student.name}
        description={`${student.level} saxophonist · personalize assignments below.`}
        actions={
          <button
            type="button"
            className="rounded-xl bg-brand-dark px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand"
          >
            Add assignment
          </button>
        }
      />

      <section className="grid gap-6 lg:grid-cols-2">
        <article className="space-y-3 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Lesson log</h2>
          <ul className="space-y-2 text-sm text-slate-600">
            <li>Last lesson: Reviewed Concert G major scale, focused on long-tone breath support.</li>
            <li>Homework: 10-minute chromatic warmup, 3x scale reps with tuner guidance.</li>
          </ul>
        </article>

        <article className="space-y-3 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Goals</h2>
          <ul className="space-y-2 text-sm text-slate-600">
            {student.goals.map((goal) => (
              <li key={goal} className="flex items-start gap-2">
                <span className="mt-1 inline-flex h-2 w-2 rounded-full bg-brand-dark" aria-hidden />
                <span>{goal}</span>
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-xl border border-brand-dark px-3 py-2 text-sm font-medium text-brand-dark transition hover:bg-brand-light"
          >
            Update goals
          </button>
        </article>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Recent practice sessions</h2>
        <div className="mt-4 grid gap-3 text-sm text-slate-600">
          <div className="flex flex-col gap-2 rounded-2xl border border-slate-100 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="font-semibold text-slate-900">Guided session · Concert G Major</p>
              <p>Time spent: 18 minutes</p>
            </div>
            <span>Completed yesterday · Notes: "Need help with second octave"</span>
          </div>
          <div className="flex flex-col gap-2 rounded-2xl border border-slate-100 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="font-semibold text-slate-900">Metronome drill · Quarter = 80</p>
              <p>Time spent: 12 minutes</p>
            </div>
            <span>Completed 3 days ago · Notes: "Struggled with crossing break"</span>
          </div>
        </div>
      </section>
    </div>
  );
}
