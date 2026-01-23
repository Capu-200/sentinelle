import Link from "next/link";
import { ArrowRight, CreditCard, Download, MoreHorizontal, Plus, Send, Wallet } from "lucide-react";
import { TransactionItem } from "@/components/transactions/transaction-item";
import { Transaction, TransactionStatus } from "@/types/transaction";
import { GlassCard } from "@/components/ui/glass-card";
import { ActionButton } from "@/components/ui/action-button";
import { AnalyticsChart } from "@/components/ui/chart";
import { cn } from "@/lib/utils";

export default function Home() {
  // Mock Data
  const recentTransactions: Transaction[] = [
    {
      id: "1",
      amount: 120.0,
      recipient: "Alice Martin",
      status: TransactionStatus.VALIDATED,
      date: new Date().toISOString(),
    },
    {
      id: "2",
      amount: 45.5,
      recipient: "Uber Eats",
      status: TransactionStatus.PENDING,
      date: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: "3",
      amount: 450.0,
      recipient: "Loyer",
      status: TransactionStatus.REJECTED,
      date: new Date(Date.now() - 172800000).toISOString(),
    },
    {
      id: "4",
      amount: 12.90,
      recipient: "Spotify",
      status: TransactionStatus.VALIDATED,
      date: new Date(Date.now() - 200000000).toISOString(),
    },
  ];

  const quickUsers = [
    { name: "Alice", avatar: "A", color: "bg-pink-100 text-pink-600 dark:bg-pink-900/40 dark:text-pink-400" },
    { name: "Bob", avatar: "B", color: "bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400" },
    { name: "Charlie", avatar: "C", color: "bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400" },
    { name: "David", avatar: "D", color: "bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400" },
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">

      {/* Header with Greeting - Desktop Visible */}
      <div className="flex items-center justify-between px-1">
        <div>
          <p className="text-sm text-muted-foreground">Bonjour,</p>
          <h1 className="text-3xl font-bold tracking-tight">Jacques</h1>
        </div>
        <div className="h-10 w-10 rounded-full bg-slate-200 dark:bg-slate-800 lg:hidden" />
      </div>

      {/* BENTO GRID LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column (Cards & Quick Actions) */}
        <div className="lg:col-span-2 space-y-6">

          {/* Main Stats Area */}
          <GlassCard gradient className="p-8 h-48 flex flex-col justify-between shadow-2xl shadow-indigo-500/20 transform transition-transform hover:scale-[1.01] cursor-pointer relative overflow-hidden">
            {/* Decorative BG pattern */}
            <div className="absolute right-0 top-0 h-full w-1/2 bg-gradient-to-l from-white/10 to-transparent pointer-events-none" />

            <div className="flex justify-between items-start z-10">
              <div>
                <p className="text-indigo-100 text-sm font-medium mb-1">Solde total disponible</p>
                <p className="text-5xl font-bold tracking-tight text-white">2 450,00 €</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-md">
                <Wallet className="text-white h-6 w-6" />
              </div>
            </div>

            <div className="flex justify-between items-end z-10">
              <div className="flex items-center gap-4 text-indigo-100">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-white/50" />
                  <div className="w-2 h-2 rounded-full bg-white/50" />
                  <div className="w-2 h-2 rounded-full bg-white/50" />
                  <div className="w-2 h-2 rounded-full bg-white" />
                </div>
                <span className="text-sm font-mono opacity-80">4242</span>
              </div>
              <div className="text-xs font-bold font-mono text-white/90 bg-white/20 px-3 py-1 rounded-lg border border-white/10">
                VISA PLATINUM
              </div>
            </div>
          </GlassCard>

          {/* Actions Row */}
          <div className="grid grid-cols-2 md:grid-cols-1 gap-6">

            {/* Quick Actions */}
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider px-1">Actions</h2>
              <div className="grid grid-cols-2 gap-4">
                <ActionButton icon={Send} label="Envoyer" href="/transfer" variant="accent" />
                <ActionButton icon={Download} label="Recevoir" href="/receive" />
              </div>
            </div>

            {/* Quick Send (Favorites) */}
            <div className="space-y-4">
              <div className="flex items-center justify-between px-1">
                <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Favoris</h2>
                <Link href="/contacts" className="text-xs text-indigo-600 font-medium hover:underline">Gérer</Link>
              </div>

              <div className="flex gap-3 overflow-x-auto pb-4 px-1 scrollbar-hide">
                <Link href="/contacts" className="flex flex-col items-center gap-2 min-w-[60px] cursor-pointer group">
                  <div className="h-14 w-14 rounded-2xl border-2 border-dashed border-slate-300 dark:border-slate-700 flex items-center justify-center text-slate-400 hover:text-indigo-600 hover:border-indigo-600 transition-colors bg-slate-50 dark:bg-slate-900">
                    <Plus className="h-6 w-6" />
                  </div>
                  <span className="text-xs font-medium text-muted-foreground group-hover:text-indigo-600">Ajouter</span>
                </Link>

                {quickUsers.map((u, i) => (
                  <Link key={i} href="/transfer" className="flex flex-col items-center gap-2 min-w-[60px] group">
                    <div className={cn("h-14 w-14 rounded-2xl flex items-center justify-center font-bold text-lg shadow-sm group-hover:scale-105 transition-all", u.color)}>
                      {u.avatar}
                    </div>
                    <span className="text-xs font-medium text-slate-700 dark:text-slate-300 group-hover:text-foreground">{u.name}</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (Transactions Feed) */}
        <div className="lg:col-span-1">
          <div className="bg-white/50 dark:bg-slate-900/50 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 backdrop-blur-sm h-full">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold">Activité récente</h2>
              <Link href="/activity" className="text-sm text-indigo-600 hover:text-indigo-500 font-medium flex items-center gap-1">
                Tout voir <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
            <div className="flex flex-col gap-2">
              {recentTransactions.map((t) => (
                <TransactionItem key={t.id} transaction={t} />
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
