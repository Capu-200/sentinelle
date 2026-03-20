"use client";

import { Check, X, Clock, Send, HandCoins, MessageSquare, ArrowDown, ArrowUp } from "lucide-react";
import { actionRespondRequest } from "@/app/actions/request";
import { useTransition, useOptimistic } from "react";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";

interface RequestItem {
    id: string;
    to?: string;
    from?: string;
    from_name?: string;
    amount: number;
    comment: string;
    status: string;
    direction: "SENT" | "RECEIVED";
    date: string;
}

interface Props {
    requests: RequestItem[];
}

function ReceivedCard({ req }: { req: RequestItem }) {
    const router = useRouter();
    const [isPending, startTransition] = useTransition();
    const [dismissed, setDismissed] = useOptimistic(false);

    const handleAction = (action: "ACCEPT" | "DECLINE") => {
        startTransition(async () => {
            setDismissed(true);
            await actionRespondRequest(req.id, action);
            router.refresh();
        });
    };

    if (dismissed) return null;

    return (
        <div className="rounded-3xl border-2 border-indigo-200 dark:border-indigo-800/60 bg-gradient-to-br from-indigo-50 to-white dark:from-indigo-950/40 dark:to-slate-900/60 p-5 shadow-sm shadow-indigo-100 dark:shadow-none">
            {/* Header badge */}
            <div className="flex items-center gap-2 mb-4">
                <div className="h-7 w-7 rounded-xl bg-indigo-600 dark:bg-indigo-500 flex items-center justify-center shadow-md shadow-indigo-300/40 dark:shadow-none">
                    <ArrowDown className="h-4 w-4 text-white" />
                </div>
                <span className="text-xs font-black uppercase tracking-widest text-indigo-600 dark:text-indigo-400">
                    Demande reçue · À vous de payer
                </span>
            </div>

            <div className="flex justify-between items-start gap-3">
                <div className="flex flex-col gap-1">
                    <p className="text-base font-black text-slate-900 dark:text-white leading-tight">
                        {req.from_name || req.from || "Inconnu"}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                        vous demande de l'argent
                    </p>
                    {req.comment && (
                        <div className="flex gap-1.5 items-start mt-2 bg-white/70 dark:bg-slate-800/50 rounded-lg px-3 py-2 border border-indigo-100 dark:border-indigo-900/30">
                            <MessageSquare className="h-3.5 w-3.5 text-indigo-400 shrink-0 mt-0.5" />
                            <p className="text-xs italic text-slate-500 dark:text-slate-400">{req.comment}</p>
                        </div>
                    )}
                </div>
                <div className="text-right shrink-0">
                    <p className="font-black text-2xl text-slate-900 dark:text-white leading-none tracking-tight">
                        {req.amount.toLocaleString()}
                    </p>
                    <p className="text-xs font-semibold text-slate-400 mt-0.5">PYC</p>
                </div>
            </div>

            <div className="mt-4 flex gap-2">
                <button
                    onClick={() => handleAction("ACCEPT")}
                    disabled={isPending}
                    className="flex-1 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-700 active:scale-95 disabled:opacity-60 text-white text-sm font-bold shadow-lg shadow-indigo-500/30 transition-all flex items-center justify-center gap-2"
                >
                    <Check className="h-4 w-4" />
                    Payer maintenant
                </button>
                <button
                    onClick={() => handleAction("DECLINE")}
                    disabled={isPending}
                    className="px-4 py-3 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 hover:border-red-200 active:scale-95 text-sm font-bold transition-all"
                >
                    <X className="h-4 w-4" />
                </button>
            </div>
        </div>
    );
}

function SentCard({ req }: { req: RequestItem }) {
    return (
        <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 p-5">
            {/* Header badge */}
            <div className="flex items-center gap-2 mb-4">
                <div className="h-7 w-7 rounded-xl bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
                    <ArrowUp className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                </div>
                <span className="text-xs font-black uppercase tracking-widest text-emerald-600 dark:text-emerald-400">
                    Demande envoyée · En attente
                </span>
            </div>

            <div className="flex justify-between items-start gap-3">
                <div className="flex flex-col gap-1">
                    <p className="text-base font-black text-slate-900 dark:text-white leading-tight">
                        {req.to}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                        doit vous envoyer de l'argent
                    </p>
                    {req.comment && (
                        <div className="flex gap-1.5 items-start mt-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg px-3 py-2 border border-slate-100 dark:border-slate-700/50">
                            <MessageSquare className="h-3.5 w-3.5 text-slate-400 shrink-0 mt-0.5" />
                            <p className="text-xs italic text-slate-500 dark:text-slate-400">{req.comment}</p>
                        </div>
                    )}
                </div>
                <div className="text-right shrink-0">
                    <p className="font-black text-2xl text-emerald-600 dark:text-emerald-400 leading-none tracking-tight">
                        +{req.amount.toLocaleString()}
                    </p>
                    <p className="text-xs font-semibold text-slate-400 mt-0.5">PYC</p>
                </div>
            </div>

            <div className="mt-4">
                <div className="flex items-center justify-center gap-2 py-2.5 rounded-2xl bg-slate-100 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 text-xs font-bold border border-slate-200/50 dark:border-slate-700/50">
                    <Clock className="h-3.5 w-3.5" />
                    En attente de paiement
                </div>
            </div>
        </div>
    );
}

export function PendingRequestsWidget({ requests }: Props) {
    const pendingReqs = requests.filter(r => r.status === "PENDING");
    const resolvedSent = requests.filter(r => r.direction === "SENT" && r.status !== "PENDING");
    const received = pendingReqs.filter(r => r.direction === "RECEIVED");
    const sent = pendingReqs.filter(r => r.direction === "SENT");

    if (pendingReqs.length === 0 && resolvedSent.length === 0) return null;

    return (
        <div className="space-y-3">
            {received.length > 0 && (
                <div className="space-y-3">
                    {received.map(req => <ReceivedCard key={req.id} req={req} />)}
                </div>
            )}

            {sent.length > 0 && (
                <div className="space-y-3">
                    {sent.map(req => <SentCard key={req.id} req={req} />)}
                </div>
            )}

            {/* Resolved sent requests */}
            {resolvedSent.length > 0 && (
                <div className="space-y-2">
                    {resolvedSent.map(req => (
                        <div key={req.id} className={cn(
                            "flex items-center justify-between px-4 py-3 rounded-2xl border text-sm font-medium",
                            req.status === "ACCEPTED"
                                ? "bg-emerald-50 border-emerald-100 dark:bg-emerald-900/20 dark:border-emerald-800/30 text-emerald-700 dark:text-emerald-400"
                                : "bg-slate-100 border-slate-200 dark:bg-slate-800/50 dark:border-slate-700 text-slate-500 dark:text-slate-400"
                        )}>
                            <div className="flex items-center gap-3">
                                {req.status === "ACCEPTED"
                                    ? <Check className="h-4 w-4 shrink-0" />
                                    : <X className="h-4 w-4 shrink-0" />
                                }
                                <div>
                                    <p className="font-semibold leading-tight">
                                        {req.status === "ACCEPTED" ? "Demande acceptée" : "Demande refusée"}
                                    </p>
                                    <p className="text-xs opacity-70 mt-0.5">
                                        {req.to} · {req.amount.toLocaleString()} PYC
                                    </p>
                                </div>
                            </div>
                            <span className={cn(
                                "text-xs font-black uppercase px-2 py-1 rounded-lg",
                                req.status === "ACCEPTED" ? "bg-emerald-100 dark:bg-emerald-900/40" : "bg-slate-200 dark:bg-slate-700"
                            )}>
                                {req.status === "ACCEPTED" ? "Payé ✓" : "Refusé"}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
