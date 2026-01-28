import Link from "next/link";
import { ArrowRight, CreditCard, Download, MoreHorizontal, Plus, Send, Wallet } from "lucide-react";
import { TransactionItem } from "@/components/transactions/transaction-item";
import { Transaction, TransactionStatus } from "@/types/transaction";
import { GlassCard } from "@/components/ui/glass-card";
import { ActionButton } from "@/components/ui/action-button";
import { AnalyticsChart } from "@/components/ui/chart";
import { cn } from "@/lib/utils";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

interface DashboardData {
  user: {
    display_name: string;
    email: string;
    risk_level: string;
    trust_score: number;
  };
  wallet: {
    wallet_id: string;
    balance: number;
    currency: string;
    kyc_status: string;
  } | null;
  recent_transactions: {
    transaction_id: string;
    amount: number;
    currency: string;
    transaction_type: string;
    direction: string;
    status: string;
    recipient_name: string;
    created_at: string;
  }[];
  contacts?: {
    name: string;
    email?: string;
    iban?: string;
    is_internal: boolean;
  }[];
}

const API_URL = process.env.API_URL || "https://sentinelle-api-backend-8773685706613.europe-west1.run.app";

async function getDashboardData(): Promise<DashboardData | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get("auth-token");

  if (!token) return null;

  try {
    const res = await fetch(`${API_URL}/dashboard/`, {
      headers: {
        "Authorization": `Bearer ${token.value}`,
        "Content-Type": "application/json"
      },
      cache: "no-store",
    });

    if (!res.ok) {
      console.error(`Dashboard Fetch Error: ${res.status} ${res.statusText}`);
      const text = await res.text();
      console.error(`Response Body: ${text}`);
      if (res.status === 401) return null;
      return null;
    }

    return await res.json();
  } catch (error) {
    console.error("Dashboard network error details:", error);
    return null;
  }
}

export default async function Home() {
  const dashboardData = await getDashboardData();

  if (!dashboardData) {
    redirect("/login");
  }

  const { user, wallet, recent_transactions, contacts } = dashboardData;

  const recentTransactions: Transaction[] = recent_transactions.map(t => ({
    id: t.transaction_id,
    amount: t.amount,
    recipient: t.recipient_name || "Inconnu",
    status: t.status as TransactionStatus,
    date: t.created_at,
    direction: t.direction as 'INCOMING' | 'OUTGOING' // Explicitly map direction
  }));

  const formatCurrency = (amount: number, currency: string) => {
    // If currency is PYC, just append string. Otherwise use intl.
    if (currency === "PYC" || currency === "EUR") { // Treating legacy EUR as PYC for display consistency if any remains
      return new Intl.NumberFormat('fr-FR', { style: 'decimal', minimumFractionDigits: 2 }).format(amount) + " PYC";
    }
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: currency }).format(amount);
  };

  // Helper for Risk Level Badge
  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case "LOW": return "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400 border-green-200 dark:border-green-500/30";
      case "MEDIUM": return "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400 border-yellow-200 dark:border-yellow-500/30";
      case "HIGH": return "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400 border-red-200 dark:border-red-500/30";
      default: return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400";
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">

      {/* Header with Greeting & Trust Score */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 px-1">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">Bonjour,</p>
            <span className={cn("text-xs px-2.5 py-0.5 rounded-full border font-bold tracking-wide", getRiskBadgeColor(user.risk_level))}>
              {user.risk_level === 'LOW' ? 'VÉRIFIÉ' : user.risk_level}
            </span>
          </div>
          <h1 className="text-3xl font-black tracking-tight text-slate-900 dark:text-white">
            {user.display_name}
          </h1>
        </div>

        {/* Trust Score Indicator */}
        <div className="flex items-center gap-4 bg-white dark:bg-slate-900 p-3 pr-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
          <div className="relative h-12 w-12 flex items-center justify-center">
            {/* Simple SVG Circular Progress */}
            <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
              <path className="text-slate-100 dark:text-slate-800" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
              <path className="text-indigo-600 transition-all duration-1000 ease-out" strokeDasharray={`${user.trust_score}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
            <span className="absolute text-xs font-bold text-indigo-600">{user.trust_score}</span>
          </div>
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase tracking-wider">Score de Confiance</p>
            <p className="text-sm font-bold text-slate-900 dark:text-white">Excellent</p>
          </div>
        </div>
      </div>

      {/* BENTO GRID LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column (Cards & Quick Actions) */}
        <div className="lg:col-span-2 space-y-6">

          {/* Main Stats Area - Wallet Card */}
          <GlassCard className="p-0 min-h-[240px] relative overflow-hidden group shadow-2xl shadow-indigo-500/20 border-0 flex flex-col">
            {/* Background Layers - Guaranteed to cover */}
            <div className="absolute inset-0 bg-gradient-to-br from-[#4f46e5] via-[#7c3aed] to-[#db2777] z-0 h-full w-full" />
            <div className="absolute inset-0 opacity-20 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] z-0 mix-blend-overlay h-full w-full" />
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-white/20 blur-[80px] rounded-full pointer-events-none" />
            <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-indigo-900/40 blur-[80px] rounded-full pointer-events-none" />

            {/* Card Content Container */}
            <div className="relative z-10 h-full flex flex-col justify-between p-7">

              {/* Top Row: Chip & Contactless & Logo */}
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-4">
                  {/* Chip */}
                  <div className="w-12 h-9 rounded-md bg-gradient-to-br from-yellow-100 to-yellow-400 border border-yellow-500/30 shadow-sm relative overflow-hidden">
                    <div className="absolute inset-0 opacity-50 border-[0.5px] border-black/10 rounded-[2px] m-[2px]" />
                    <div className="absolute top-[50%] left-0 right-0 h-[1px] bg-black/10" />
                    <div className="absolute left-[33%] top-0 bottom-0 w-[1px] bg-black/10" />
                    <div className="absolute right-[33%] top-0 bottom-0 w-[1px] bg-black/10" />
                  </div>
                  {/* Contactless Icon */}
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-white/70 transform rotate-90 scale-110 opacity-70" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"></path><path d="M1.42 9a16 16 0 0 1 21.16 0"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path></svg>
                </div>

                {/* Visa Logo (White Text) */}
                <div className="italic font-black text-2xl text-white tracking-tighter opacity-90 pr-1">VISA</div>
              </div>

              {/* Middle Row: Balance */}
              <div className="space-y-1 mt-4">
                <p className="text-indigo-100/80 text-[10px] font-bold uppercase tracking-[0.2em] ml-1">Solde disponible</p>
                <p className="text-4xl md:text-5xl font-bold tracking-tight text-white drop-shadow-lg tabular-nums">
                  {wallet ? formatCurrency(wallet.balance, wallet.currency) : "---"}
                </p>
              </div>

              {/* Bottom Row: Card Details */}
              <div className="flex justify-between items-end mt-2">
                <div className="space-y-1.5">
                  <div className="flex gap-3 text-white/90 text-lg font-mono tracking-[0.15em] drop-shadow-md items-center">
                    <span className="opacity-60 text-base flex gap-1">
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                    </span>
                    <span className="opacity-60 text-base flex gap-1">
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                    </span>
                    <span className="opacity-60 text-base flex gap-1">
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                      <span className="bg-white rounded-full w-1.5 h-1.5 inline-block" />
                    </span>
                    <span className="font-bold">{wallet ? wallet.wallet_id.slice(-4) : "0000"}</span>
                  </div>
                  <p className="text-[11px] font-bold text-indigo-100/90 uppercase tracking-widest pl-1">{user.display_name}</p>
                </div>

                {/* Platinum Label */}
                <div className="text-[9px] font-bold text-white/60 uppercase tracking-widest border border-white/20 rounded px-2 py-0.5">Platinum</div>
              </div>

            </div>
          </GlassCard>

          {/* Actions Row */}
          <div className="grid grid-cols-1 gap-6">
            {/* Quick Actions */}
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-1">Accès Rapide</h2>
              <div className="grid grid-cols-2 gap-4">
                <ActionButton icon={Send} label="Envoyer" href="/transfer" variant="accent" />
                <ActionButton icon={Download} label="Recevoir" href="/receive" />
              </div>
            </div>

            {/* Favorites */}
            <div className="space-y-4">
              <div className="flex items-center justify-between px-1">
                <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Favoris</h2>
                <Link href="/contacts" className="text-xs text-indigo-600 font-bold hover:text-indigo-500 transition-colors">Gérer</Link>
              </div>

              <div className="flex gap-3 overflow-x-auto pb-4 px-1 scrollbar-hide">
                <Link href="/contacts" className="flex flex-col items-center gap-2 min-w-[64px] cursor-pointer group">
                  <div className="h-16 w-16 rounded-2xl border-2 border-dashed border-slate-300 dark:border-slate-700 flex items-center justify-center text-slate-400 hover:text-indigo-600 hover:border-indigo-600 transition-all bg-slate-50 dark:bg-slate-900 group-hover:scale-105">
                    <Plus className="h-6 w-6" />
                  </div>
                  <span className="text-xs font-medium text-slate-500 group-hover:text-indigo-600 transition-colors">Ajouter</span>
                </Link>

                {contacts && contacts.length > 0 ? (
                  contacts.slice(0, 5).map((c, i) => (
                    <Link key={i} href={`/transfer?to=${c.email || c.iban}`} className="flex flex-col items-center gap-2 min-w-[64px] group">
                      <div className={cn("h-16 w-16 rounded-2xl flex items-center justify-center font-bold text-xl shadow-sm group-hover:scale-105 group-hover:shadow-md transition-all",
                        c.is_internal ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400" : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                      )}>
                        {c.name.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase()}
                      </div>
                      <span className="text-xs font-medium text-slate-600 dark:text-slate-300 group-hover:text-indigo-600 transition-colors truncate max-w-[64px]">{c.name.split(' ')[0]}</span>
                    </Link>
                  ))
                ) : null}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (Transactions Feed) */}
        <div className="lg:col-span-1">
          <div className="bg-white/60 dark:bg-slate-900/60 rounded-3xl p-6 border border-white/20 dark:border-slate-800 shadow-xl backdrop-blur-md h-full flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Activité</h2>
              <Link href="/activity" className="text-xs font-bold text-indigo-600 hover:text-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 px-3 py-1.5 rounded-full transition-colors">
                TOUT VOIR
              </Link>
            </div>

            <div className="flex flex-col gap-3 overflow-y-auto pr-1 flex-1 custom-scrollbar" style={{ maxHeight: '600px' }}>
              {recentTransactions.length > 0 ? (
                recentTransactions.map((t) => (
                  <TransactionItem key={t.id} transaction={t} />
                ))
              ) : (
                <div className="text-center py-20 flex flex-col items-center justify-center h-full text-slate-400">
                  <div className="h-16 w-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                    <MoreHorizontal className="h-8 w-8 text-slate-300 dark:text-slate-600" />
                  </div>
                  <p className="font-medium">Aucune transaction</p>
                  <p className="text-sm opacity-70 mt-1">Vos opérations apparaîtront ici</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
