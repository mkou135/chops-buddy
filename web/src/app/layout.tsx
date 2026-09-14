import type { Metadata } from "next";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";

import { AuthProvider } from "@/lib/auth-context";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "Chops Buddy",
  description: "Structured home practice for instrumental students, and a small CRM for their teachers.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className="h-full bg-brand-light">
      <body className={`${inter.className} min-h-screen bg-white text-slate-900`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
