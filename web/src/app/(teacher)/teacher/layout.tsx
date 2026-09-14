"use client";

import type { ReactNode } from "react";

import { AppShell, type AppNavItem } from "@/components/app-shell";
import { RequireRole, useAuth } from "@/lib/auth-context";

const teacherNav: AppNavItem[] = [
  { href: "/teacher/students", label: "Students", description: "Roster and assignments" },
  { href: "/teacher/schools", label: "Schools", description: "Schools you teach at, and their terms" },
  { href: "/teacher/schedule", label: "Schedule", description: "Lessons across all students" },
];

export default function TeacherLayout({ children }: { children: ReactNode }) {
  const { profile, signOut } = useAuth();
  return (
    <AppShell
      navItems={teacherNav}
      subtitle="Teacher workspace"
      header={
        <button type="button" onClick={() => void signOut()} className="text-sm text-slate-600">
          Sign out{profile ? ` (${profile.display_name})` : ""}
        </button>
      }
    >
      <RequireRole role="teacher">{children}</RequireRole>
    </AppShell>
  );
}
