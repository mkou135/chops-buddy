import { PageHeader } from "@/components/page-header";

export default function SettingsPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Studio settings"
        description="Update your teaching profile, notification preferences, and tuner defaults."
      />

      <section className="grid gap-6 lg:grid-cols-2">
        <form className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Profile</h2>
          <label className="flex flex-col gap-2 text-sm text-slate-600">
            Display name
            <input
              className="rounded-xl border border-slate-200 px-3 py-2 text-slate-900 focus:border-brand-dark focus:outline-none focus:ring-2 focus:ring-brand/40"
              placeholder="Jamie Thompson"
              type="text"
            />
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-600">
            Studio timezone
            <select className="rounded-xl border border-slate-200 px-3 py-2 text-slate-900 focus:border-brand-dark focus:outline-none focus:ring-2 focus:ring-brand/40">
              <option>America/New_York</option>
              <option>America/Chicago</option>
              <option>America/Denver</option>
              <option>America/Los_Angeles</option>
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-600">
            Primary instrument focus
            <input
              className="rounded-xl border border-slate-200 px-3 py-2 text-slate-900 focus:border-brand-dark focus:outline-none focus:ring-2 focus:ring-brand/40"
              defaultValue="Alto saxophone"
              type="text"
            />
          </label>
          <button
            type="button"
            className="rounded-xl bg-brand-dark px-4 py-2 text-sm font-medium text-white transition hover:bg-brand"
          >
            Save profile
          </button>
        </form>

        <form className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Notifications</h2>
          <fieldset className="space-y-3 text-sm text-slate-600">
            <label className="flex items-center gap-2">
              <input defaultChecked type="checkbox" className="h-4 w-4 rounded border-slate-300 text-brand-dark focus:ring-brand" />
              Lesson reminders
            </label>
            <label className="flex items-center gap-2">
              <input defaultChecked type="checkbox" className="h-4 w-4 rounded border-slate-300 text-brand-dark focus:ring-brand" />
              Practice summaries
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-brand-dark focus:ring-brand" />
              Student questions
            </label>
          </fieldset>
          <div className="space-y-2 text-sm text-slate-600">
            <label className="flex items-center gap-2">
              <input defaultChecked type="radio" name="contact" className="h-4 w-4 border-slate-300 text-brand-dark focus:ring-brand" />
              Email
            </label>
            <label className="flex items-center gap-2">
              <input type="radio" name="contact" className="h-4 w-4 border-slate-300 text-brand-dark focus:ring-brand" />
              SMS (coming soon)
            </label>
          </div>
          <button
            type="button"
            className="rounded-xl bg-brand-dark px-4 py-2 text-sm font-medium text-white transition hover:bg-brand"
          >
            Save notifications
          </button>
        </form>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Tuner defaults</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <label className="flex flex-col gap-2 text-sm text-slate-600">
            Instrument transposition
            <select className="rounded-xl border border-slate-200 px-3 py-2 text-slate-900 focus:border-brand-dark focus:outline-none focus:ring-2 focus:ring-brand/40">
              <option>Alto (E♭)</option>
              <option>Tenor (B♭)</option>
              <option>Bari (E♭)</option>
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-600">
            Pitch tolerance (cents)
            <input
              className="rounded-xl border border-slate-200 px-3 py-2 text-slate-900 focus:border-brand-dark focus:outline-none focus:ring-2 focus:ring-brand/40"
              defaultValue="10"
              type="number"
            />
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-600">
            Metronome default tempo
            <input
              className="rounded-xl border border-slate-200 px-3 py-2 text-slate-900 focus:border-brand-dark focus:outline-none focus:ring-2 focus:ring-brand/40"
              defaultValue="80"
              type="number"
            />
          </label>
        </div>
        <button
          type="button"
          className="mt-6 rounded-xl bg-brand-dark px-4 py-2 text-sm font-medium text-white transition hover:bg-brand"
        >
          Save tuner settings
        </button>
      </section>
    </div>
  );
}
