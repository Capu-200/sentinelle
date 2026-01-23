"use client";

import { useTransactionSocket } from "@/hooks/use-transaction-socket";
import { TransactionStatus } from "@/types/transaction";
import { StatusBadge } from "@/components/ui/status-badge";
import { ArrowLeft, CheckCircle2, Circle, Clock, Loader2, ShieldAlert, ShieldCheck, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { GlassCard } from "@/components/ui/glass-card";

export default function TrackingPage() {
    const params = useParams();
    const searchParams = useSearchParams();
    const id = params.id as string;
    const amount = searchParams.get("amount") || "120.00";
    const { status } = useTransactionSocket(id);

    const steps = [
        {
            id: "sent",
            label: "Virement initié",
            description: "Demande reçue par PayOn.",
            status: "completed",
            icon: CheckCircle2,
        },
        {
            id: "analyzing",
            label: "Analyse IA",
            description: "Détection de fraude en cours...",
            status:
                status === TransactionStatus.PENDING
                    ? "current"
                    : "completed",
            icon: ShieldCheck,
        },
        {
            id: "suspect",
            label: "Examen complémentaire",
            description: "Transaction en cours de revue manuelle.",
            status: status === TransactionStatus.SUSPECT ? "error" : (status === TransactionStatus.VALIDATED || status === TransactionStatus.REJECTED ? "completed" : "upcoming"),
            icon: AlertTriangle,
            hidden: status !== TransactionStatus.SUSPECT && status !== TransactionStatus.VALIDATED && status !== TransactionStatus.REJECTED // Only show if we hit this path
        },
        {
            id: "result",
            label: "Validation finale",
            description:
                status === TransactionStatus.REJECTED
                    ? "Bloqué par sécurité."
                    : "Fonds transférés.",
            status:
                status === TransactionStatus.PENDING || status === TransactionStatus.ANALYZING || status === TransactionStatus.SUSPECT
                    ? "upcoming"
                    : status === TransactionStatus.REJECTED
                        ? "error"
                        : "success",
            icon: status === TransactionStatus.REJECTED ? ShieldAlert : CheckCircle2,
        },
    ];

    return (
        <div className="space-y-6 max-w-xl mx-auto">
            <div className="flex items-center gap-4">
                <Link
                    href="/activity"
                    className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                    <ArrowLeft className="h-6 w-6" />
                </Link>
                <div className="flex flex-col">
                    <h1 className="text-xl font-bold">Suivi de virement</h1>
                    <span className="text-xs text-muted-foreground">Réf: {id}</span>
                </div>
            </div>

            <GlassCard className="p-6">
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <p className="text-sm text-muted-foreground">Montant</p>
                        <p className="text-3xl font-bold">{amount} €</p>
                    </div>
                    <StatusBadge status={status} className="text-sm px-3 py-1 scale-110" />
                </div>

                {/* Vertical Stepper */}
                <div className="relative space-y-8 pl-4">
                    {/* Vertical Line */}
                    <div className="absolute left-[27px] top-2 bottom-4 w-0.5 bg-slate-200 dark:bg-slate-700" />

                    {steps.filter(s => !s.hidden).map((step, index) => {
                        const isCompleted = step.status === "completed" || step.status === "success";
                        const isCurrent = step.status === "current";
                        const isError = step.status === "error";

                        return (
                            <div key={step.id} className="relative flex items-start gap-4 animate-in slide-in-from-bottom-2 duration-500">
                                <div
                                    className={cn(
                                        "relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 bg-background transition-colors",
                                        isCompleted && "border-indigo-600 bg-indigo-600 text-white",
                                        isCurrent && "border-indigo-600 animate-pulse",
                                        isError && "border-orange-500 bg-orange-500 text-white",
                                        !isCompleted && !isCurrent && !isError && "border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900"
                                    )}
                                >
                                    {isCurrent && <Loader2 className="h-3 w-3 animate-spin text-indigo-600" />}
                                    {isCompleted && <CheckCircle2 className="h-4 w-4" />}
                                    {isError && <AlertTriangle className="h-4 w-4" />}
                                    {!isCompleted && !isCurrent && !isError && <Circle className="h-3 w-3 text-muted-foreground" />}
                                </div>

                                <div className={cn("flex flex-col pt-0.5", (isCurrent || isCompleted || isError) ? "opacity-100" : "opacity-50")}>
                                    <span className="font-semibold text-sm">{step.label}</span>
                                    <span className="text-xs text-muted-foreground">{step.description}</span>

                                    {/* Info Block - No Actions */}
                                    {step.id === 'suspect' && isError && (
                                        <div className="mt-4 p-4 rounded-xl bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800/50">
                                            <p className="text-sm font-medium text-orange-800 dark:text-orange-200 mb-1 flex items-center gap-2">
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                Analyse approfondie en cours
                                            </p>
                                            <p className="text-xs text-orange-700 dark:text-orange-300">
                                                Nos experts vérifient cette transaction. Aucune action n'est requise de votre part.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </GlassCard>

            {status === TransactionStatus.VALIDATED && (
                <div className="rounded-xl bg-green-50 p-4 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400 border border-green-200 dark:border-green-800 animate-in zoom-in duration-300">
                    <div className="flex items-center gap-2 font-bold mb-1">
                        <CheckCircle2 className="h-4 w-4" />
                        Virement confirmé
                    </div>
                    Le destinataire recevra les fonds instantanéement.
                </div>
            )}
        </div>
    );
}
