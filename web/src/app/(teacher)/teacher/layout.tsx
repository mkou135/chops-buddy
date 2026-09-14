import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import type { AppNavItem } from "@/components/app-shell";

const teacherNav: AppNavItem[] = [
  {
    href: "/teacher/dashboard",
    label: "Dashboard",
    description: "Studio snapshots and upcoming lessons",
  },
  {
    href: "/teacher/students",
    label: "Students",
    description: "Roster, lesson notes, and individual plans",
  },
  {
    href: "/teacher/assignments",
    label: "Assignments",
    description: "Create scale plans and monitor progress",
  },
  {
    href: "/teacher/practice",
    label: "Practice log",
    description: "Guided session summaries and metrics",
  },
  {
    href: "/teacher/questions",
    label: "Questions",
    description: "Respond to student follow-ups",
  },
  {
    href: "/teacher/settings",
    label: "Settings",
    description: "Studio profile and notifications",
  },
];

type TeacherLayoutProps = {
  children: ReactNode;
};

export default function TeacherLayout({ children }: TeacherLayoutProps) {
  return <AppShell navItems={teacherNav}>{children}</AppShell>;
}
