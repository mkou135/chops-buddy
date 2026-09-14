import type { Metadata } from "next";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "Chops Buddy",
  description: "Guided saxophone practice and studio management platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en" className="h-full bg-brand-light">
      <body className={`${inter.className} min-h-screen bg-white text-slate-900`}>
        {children}
      </body>
    </html>
  );
}
