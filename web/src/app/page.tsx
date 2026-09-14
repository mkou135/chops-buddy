"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth-context";

export default function HomePage() {
  const { ready, session, profile } = useAuth();
  const target = profile?.role === "teacher" ? "/teacher/students/" : "/student/";
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 px-6 py-16">
      <h1 className="text-3xl font-semibold text-slate-900">Chops Buddy</h1>
      <p className="text-slate-600">
        A teacher assigns targets. The engine turns them into a practice session with a tempo,
        a fragment, and a repetition goal. The student logs what happened; the next session
        follows from it.
      </p>
      {ready && session && profile ? (
        <Link href={target} className="w-fit rounded-xl bg-brand-dark px-4 py-2 text-sm font-medium text-white no-underline">
          Continue as {profile.display_name}
        </Link>
      ) : (
        <Link href="/sign-in/" className="w-fit rounded-xl bg-brand-dark px-4 py-2 text-sm font-medium text-white no-underline">
          Sign in
        </Link>
      )}
      <p className="text-xs text-slate-500">
        Source, spec, and eval results: <a href="https://github.com/mkou135/chops-buddy">github.com/mkou135/chops-buddy</a>
      </p>
    </main>
  );
}
