import { PageHeader } from "@/components/page-header";

const questions = [
  {
    student: "Alex Rivera",
    question: "Can we review alternate fingerings for the top F?",
    submitted: "1 hour ago",
    assignment: "Concert G Major scale",
  },
  {
    student: "Maya Chen",
    question: "What tempo should I use when practicing with the metronome?",
    submitted: "Yesterday",
    assignment: "Chromatic warmup",
  },
  {
    student: "Jordan Smith",
    question: "Is it okay to record the tuner feedback to compare takes?",
    submitted: "2 days ago",
    assignment: "Long-tone breath builder",
  },
];

export default function QuestionsPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Student questions"
        description="Respond quickly to keep students motivated between lessons."
        actions={
          <button
            type="button"
            className="rounded-xl border border-brand-dark px-4 py-2 text-sm font-medium text-brand-dark transition hover:bg-brand-light"
          >
            Mark all as read
          </button>
        }
      />

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Inbox</h2>
          <div className="flex flex-wrap gap-2 text-sm">
            <button className="rounded-xl border border-brand-dark px-3 py-2 text-brand-dark transition hover:bg-brand-light" type="button">
              Filter by assignment
            </button>
            <button className="rounded-xl border border-brand-dark px-3 py-2 text-brand-dark transition hover:bg-brand-light" type="button">
              Show resolved
            </button>
          </div>
        </div>
        <div className="grid gap-4">
          {questions.map((item) => (
            <article key={item.question} className="space-y-3 rounded-2xl border border-slate-100 bg-slate-50 p-4">
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                  <h3 className="text-base font-semibold text-slate-900">{item.student}</h3>
                  <p className="text-sm text-slate-600">{item.assignment}</p>
                </div>
                <span className="text-sm text-slate-500">{item.submitted}</span>
              </div>
              <p className="text-sm text-slate-700">{item.question}</p>
              <div className="flex flex-wrap gap-2">
                <button className="rounded-xl bg-brand-dark px-3 py-2 text-sm font-medium text-white transition hover:bg-brand" type="button">
                  Reply
                </button>
                <button className="rounded-xl border border-brand-dark px-3 py-2 text-sm font-medium text-brand-dark transition hover:bg-brand-light" type="button">
                  Archive
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
