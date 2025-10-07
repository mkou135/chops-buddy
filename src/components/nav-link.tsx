"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

type NavLinkProps = {
  href: string;
  label: string;
};

export function NavLink({ href, label }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      className={cn(
        "flex items-center justify-between gap-2 rounded-xl px-4 py-2 text-sm font-medium transition",
        isActive
          ? "bg-brand-dark text-white shadow-sm"
          : "text-slate-600 hover:bg-brand-light hover:text-brand-dark"
      )}
    >
      <span>{label}</span>
      {isActive ? <span className="text-xs uppercase tracking-wide">Now</span> : null}
    </Link>
  );
}
