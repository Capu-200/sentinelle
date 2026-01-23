'use client';

import { useState, useMemo } from 'react';
import { TransactionItem } from "@/components/transactions/transaction-item";
import { Transaction, TransactionStatus } from "@/types/transaction";
import { ArrowLeft, Search, Filter, ArrowDownUp, ArrowUpRight, ArrowDownLeft } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";

export default function ActivityPage() {
    const [searchTerm, setSearchTerm] = useState("");
    const [filter, setFilter] = useState<'ALL' | 'IN' | 'OUT'>('ALL');

    // Enhanced Mock Data
    const rawTransactions: Transaction[] = Array.from({ length: 15 }).map((_, i) => {
        const isIncoming = Math.random() > 0.6;
        return {
            id: `hist-${i}`,
            amount: Math.floor(Math.random() * 500) + 10,
            recipient: isIncoming ? `Virement de Jean` : (Math.random() > 0.5 ? `Netflix` : `Uber Eats`),
            status: Math.random() > 0.8 ? TransactionStatus.PENDING : TransactionStatus.VALIDATED,
            date: new Date(Date.now() - i * i * 3600000 * 5).toISOString(), // Spread out dates
        };
    });

    // Filtering Logic
    const filteredTransactions = useMemo(() => {
        return rawTransactions.filter(t => {
            const matchesSearch = t.recipient.toLowerCase().includes(searchTerm.toLowerCase());
            const matchesFilter =
                filter === 'ALL' ? true :
                    filter === 'IN' ? t.recipient.startsWith('Virement') : // Simple mock logic for In/Out
                        !t.recipient.startsWith('Virement');

            return matchesSearch && matchesFilter;
        });
    }, [searchTerm, filter, rawTransactions]);

    // Grouping Logic
    const groupedTransactions = useMemo(() => {
        const groups: Record<string, Transaction[]> = {};

        filteredTransactions.forEach(t => {
            const date = new Date(t.date);
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);

            let key = date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });

            if (date.toDateString() === today.toDateString()) key = "Aujourd'hui";
            if (date.toDateString() === yesterday.toDateString()) key = "Hier";

            if (!groups[key]) groups[key] = [];
            groups[key].push(t);
        });

        return groups;
    }, [filteredTransactions]);

    return (
        <div className="space-y-6 max-w-2xl mx-auto">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link href="/" className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                    <ArrowLeft className="h-6 w-6" />
                </Link>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold">Historique</h1>
                    <p className="text-sm text-muted-foreground">Vos dernières transactions</p>
                </div>
            </div>

            {/* Controls */}
            <div className="sticky top-20 z-30 space-y-4">
                {/* Search */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Rechercher une transaction..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 rounded-xl border-none bg-white dark:bg-slate-900 shadow-sm ring-1 ring-slate-200 dark:ring-slate-800 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                    />
                </div>

                {/* Filters */}
                <div className="flex p-1 bg-slate-100 dark:bg-slate-900 rounded-xl">
                    {[
                        { key: 'ALL', label: 'Tout', icon: ArrowDownUp },
                        { key: 'OUT', label: 'Dépenses', icon: ArrowUpRight },
                        { key: 'IN', label: 'Entrées', icon: ArrowDownLeft },
                    ].map(tab => (
                        <button
                            key={tab.key}
                            onClick={() => setFilter(tab.key as any)}
                            className={cn(
                                "flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium rounded-lg transition-all",
                                filter === tab.key
                                    ? "bg-white dark:bg-slate-800 text-indigo-600 shadow-sm"
                                    : "text-muted-foreground hover:text-foreground"
                            )}
                        >
                            <tab.icon className="h-4 w-4" />
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Grouped List */}
            <div className="space-y-6 pb-20">
                {Object.entries(groupedTransactions).map(([date, txs]) => (
                    <div key={date} className="space-y-3">
                        <h3 className="text-sm font-semibold text-muted-foreground sticky top-[160px] bg-slate-50/80 dark:bg-[#050505]/80 backdrop-blur-sm py-2 px-1 z-20">
                            {date}
                        </h3>
                        <GlassCard className="p-1 overflow-hidden">
                            <div className="divide-y divide-slate-100 dark:divide-slate-800/50">
                                {txs.map((t) => (
                                    <div key={t.id} className="p-2 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors rounded-lg">
                                        <TransactionItem transaction={t} />
                                    </div>
                                ))}
                            </div>
                        </GlassCard>
                    </div>
                ))}

                {Object.keys(groupedTransactions).length === 0 && (
                    <div className="text-center py-12 text-muted-foreground">
                        <Search className="h-12 w-12 mx-auto mb-4 opacity-20" />
                        <p>Aucune transaction trouvée</p>
                    </div>
                )}
            </div>
        </div>
    );
}
