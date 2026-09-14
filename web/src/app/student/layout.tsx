"use client";

import type { ReactNode } from "react";

import { AppShell, type AppNavItem } from "@/components/app-shell";
import { RequireRole, useAuth } from "@/lib/auth-context";

const nav: AppNavItem[] = [
  { href: "/student", label: "Practise", description: "Your next session" },
  { href: "/student/history", label: "History", description: "What you logged" },
];

export default function StudentLayout({ children }: { children: ReactNode }) {
  const { profile, signOut } = useAuth();
  return (
    <AppShell
      navItems={nav}
      subtitle="Student"
      header={
        <button type="button" onClick={() => void signOut()} className="text-sm text-slate-600">
          Sign out{profile ? ` (${profile.display_name})` : ""}
        </button>
      }
    >
      <RequireRole role="student">{children}</RequireRole>
    </AppShell>
  );
}
