"use client";

import { useState, useMemo } from 'react';
import { TransactionItem } from "@/components/transactions/transaction-item";
import { Transaction, TransactionStatus } from "@/types/transaction";
import { Search, ArrowDownUp, ArrowUpRight, ArrowDownLeft, MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";

interface ActivityListProps {
    initialTransactions: Transaction[];
}

export function ActivityList({ initialTransactions }: ActivityListProps) {
    const [searchTerm, setSearchTerm] = useState("");
    const [filter, setFilter] = useState<'ALL' | 'IN' | 'OUT'>('ALL');

    // Filtering Logic
    const filteredTransactions = useMemo(() => {
        return initialTransactions.filter(t => {
            const matchesSearch = t.recipient.toLowerCase().includes(searchTerm.toLowerCase());

            let matchesFilter = true;
            if (filter === 'OUT') {
                matchesFilter = t.direction === 'OUTGOING';
            } else if (filter === 'IN') {
                matchesFilter = t.direction === 'INCOMING';
            }

            return matchesSearch && matchesFilter;
        });
    }, [searchTerm, filter, initialTransactions]);

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
        <div className="space-y-6">
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
                        <div className="h-16 w-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-4">
                            <MoreHorizontal className="h-8 w-8 text-slate-300 dark:text-slate-600" />
                        </div>
                        <p>Aucune transaction trouvée</p>
                    </div>
                )}
            </div>
        </div>
    );
}
