import type { ReactNode } from "react";

import { NavLink } from "@/components/nav-link";

export type AppNavItem = {
  href: string;
  label: string;
  description?: string;
};

type AppShellProps = {
  children: ReactNode;
  navItems: AppNavItem[];
  header?: ReactNode;
  footer?: ReactNode;
};

export function AppShell({ children, navItems, header, footer }: AppShellProps) {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex flex-col">
            <span className="text-sm font-semibold uppercase tracking-wide text-brand-dark">
              Chops Buddy
            </span>
            <span className="text-base text-slate-500">Teacher workspace</span>
          </div>
          {header}
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-10 lg:flex-row">
        <aside className="lg:w-64">
          <nav className="flex flex-row gap-3 overflow-x-auto rounded-2xl border border-slate-200 bg-white p-3 lg:flex-col lg:gap-2">
            {navItems.map((item) => (
              <div key={item.href} className="min-w-[10rem]">
                <NavLink href={item.href} label={item.label} />
                {item.description ? (
                  <p className="mt-2 hidden text-xs text-slate-500 lg:block">{item.description}</p>
                ) : null}
              </div>
            ))}
          </nav>
        </aside>

        <main className="flex-1 space-y-8">
          {children}
          {footer ? <div className="border-t border-slate-200 pt-6 text-sm text-slate-500">{footer}</div> : null}
        </main>
      </div>
    </div>
  );
}
