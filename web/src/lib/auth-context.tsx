"use client";

import type { Session as SupabaseSession } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { ApiError, createApi, type Api, type Profile } from "@/lib/api";
import { supabase } from "@/lib/supabase-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type AuthState = {
  ready: boolean;
  session: SupabaseSession | null;
  profile: Profile | null;
  api: Api;
  refreshProfile: () => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [session, setSession] = useState<SupabaseSession | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);

  const api = useMemo(
    () =>
      createApi(API_URL, async () => {
        if (!supabase) return null;
        const { data } = await supabase.auth.getSession();
        return data.session?.access_token ?? null;
      }),
    [],
  );

  async function refreshProfile() {
    try {
      setProfile(await api.me());
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) setProfile(null);
      else throw err;
    }
  }

  useEffect(() => {
    if (!supabase) {
      setReady(true);
      return;
    }
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setReady(true);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
      setProfile(null);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (session) void refreshProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.access_token]);

  const value: AuthState = {
    ready,
    session,
    profile,
    api,
    refreshProfile,
    signOut: async () => {
      await supabase?.auth.signOut();
    },
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

/** Redirects to sign-in unless a signed-in user with the given role is present. */
export function RequireRole({ role, children }: { role: Profile["role"]; children: ReactNode }) {
  const { ready, session, profile } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (ready && !session) router.replace("/sign-in/");
  }, [ready, session, router]);
  if (!ready || !session) return <p className="text-sm text-slate-500">Loading…</p>;
  if (!profile) return <p className="text-sm text-slate-500">Loading profile…</p>;
  if (profile.role !== role) {
    return (
      <p className="text-sm text-red-700">
        Signed in as a {profile.role}; this page is for {role}s.
      </p>
    );
  }
  return <>{children}</>;
}
