import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/layout/app-shell";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PAYONE - Banking Reinvented",
  description: "Next-gen secure payment platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="h-full">
      <body className={`${inter.className} min-h-full bg-slate-50 dark:bg-[#050505] text-slate-900 dark:text-slate-50 overflow-x-hidden selection:bg-indigo-500/30`}>
        {/* Ambient Light */}
        <div className="fixed top-[-10%] left-[-10%] h-[500px] w-[500px] rounded-full bg-indigo-600/20 blur-[120px] mix-blend-screen pointer-events-none z-0" />
        <div className="fixed bottom-[-10%] right-[-10%] h-[500px] w-[500px] rounded-full bg-purple-600/10 blur-[120px] mix-blend-screen pointer-events-none z-0" />

        <AppShell>
          {children}
        </AppShell>
      </body>
    </html>
  );
}
