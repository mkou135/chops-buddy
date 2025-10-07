import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Metadata } from "next";

function getDesignDoc() {
  const docPath = join(process.cwd(), "docs", "design.md");
  try {
    return readFileSync(docPath, "utf8");
  } catch (error) {
    console.error("Unable to load design document", error);
    return "Design document could not be loaded.";
  }
}

export const metadata: Metadata = {
  title: "Design Document | Chops Buddy",
  description: "Detailed MVP design documentation for the Chops Buddy platform.",
};

export default function DesignPage() {
  const markdown = getDesignDoc();

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-16">
      <header className="space-y-3 text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-dark">
          Documentation
        </p>
        <h1 className="text-4xl font-semibold text-slate-900">Chops Buddy MVP Design</h1>
        <p className="text-base text-slate-600">
          This document outlines goals, architecture, page flows, and rollout plans for the initial
          release.
        </p>
      </header>

      <article className="rounded-3xl bg-white p-6 shadow-lg ring-1 ring-brand-light">
        <pre className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
          {markdown}
        </pre>
      </article>
    </main>
  );
}
