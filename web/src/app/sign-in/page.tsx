"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { useAuth } from "@/lib/auth-context";
import { supabase } from "@/lib/supabase-client";

type ModeTab = "sign-in" | "sign-up";

export default function SignInPage() {
  const { api, refreshProfile } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<ModeTab>("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [role, setRole] = useState<"teacher" | "student">("student");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!supabase) {
      setError("Supabase is not configured (NEXT_PUBLIC_SUPABASE_URL / _ANON_KEY).");
      return;
    }
    setBusy(true);
    try {
      if (tab === "sign-up") {
        const { error: err } = await supabase.auth.signUp({ email, password });
        if (err) throw err;
        await api.createProfile(role, displayName || email);
      } else {
        const { error: err } = await supabase.auth.signInWithPassword({ email, password });
        if (err) throw err;
      }
      await refreshProfile();
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-6 py-16">
      <h1 className="text-2xl font-semibold">{tab === "sign-in" ? "Sign in" : "Create an account"}</h1>
      <div className="flex gap-2 text-sm">
        <button type="button" onClick={() => setTab("sign-in")} className={tab === "sign-in" ? "font-semibold" : "text-slate-500"}>
          Sign in
        </button>
        <span className="text-slate-300">|</span>
        <button type="button" onClick={() => setTab("sign-up")} className={tab === "sign-up" ? "font-semibold" : "text-slate-500"}>
          Sign up
        </button>
      </div>
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <label className="text-sm">
          Email
          <input className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="text-sm">
          Password
          <input className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {tab === "sign-up" ? (
          <>
            <label className="text-sm">
              Display name
              <input className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
            </label>
            <label className="text-sm">
              I am a
              <select className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" value={role} onChange={(e) => setRole(e.target.value as "teacher" | "student")}>
                <option value="student">student</option>
                <option value="teacher">teacher</option>
              </select>
            </label>
          </>
        ) : null}
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <button disabled={busy} className="rounded-xl bg-brand-dark px-4 py-2 text-sm font-medium text-white disabled:opacity-50" type="submit">
          {busy ? "Working…" : tab === "sign-in" ? "Sign in" : "Sign up"}
        </button>
      </form>
      <p className="text-xs text-slate-500">
        Students: your teacher must add you to their roster before a session can be generated. Sign-up links to that record in a later milestone.
      </p>
    </main>
  );
}
