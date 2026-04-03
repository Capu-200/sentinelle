import { TransactionStatus } from "@/types/transaction";
import { cn } from "@/lib/utils";
import { CheckCircle, Clock, Loader2, XCircle, AlertTriangle } from "lucide-react";

interface Props {
    status: TransactionStatus;
    className?: string;
}

export const StatusBadge = ({ status, className }: Props) => {
    const config = {
        [TransactionStatus.PENDING]: {
            label: "Traitement en cours...",
            icon: Loader2,
            style: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400",
            iconClass:"animate-spin",
        },
        [TransactionStatus.ANALYZING]: {
            label: "Analyse IA...",
            icon: Loader2,
            style: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400",
            iconClass: "animate-spin",
        },
        [TransactionStatus.SUSPECT]: {
            label: "Vérification requise",
            icon: AlertTriangle,
            style: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
            iconClass:"",
        },
        [TransactionStatus.VALIDATED]: {
            label: "Validé",
            icon: CheckCircle,
            style: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
            iconClass:"",
        },
        [TransactionStatus.REJECTED]: {
            label: "Rejeté",
            icon: XCircle,
            style: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-500",
            iconClass:"",
        },
        // Fallbacks for direct backend decision mapping
        "REVIEW": {
            label: "En revue (IA)",
            icon: AlertTriangle,
            style: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
            iconClass:"",
        },
        "BLOCK": {
            label: "Bloqué",
            icon: XCircle,
            style: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-500",
            iconClass:"",
        },
        "APPROVE": {
            label: "Validé (IA)",
            icon: CheckCircle,
            style: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
            iconClass:"",
        }
    } as any;

    const safeStatus = status || "UNKNOWN";
    const statusConfig = config[safeStatus] || {
        label: safeStatus,
        icon: Clock,
        style: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400",
        iconClass: "",
    };

    const { label, icon: Icon, style, iconClass } = statusConfig;

    return (
        <div
            className={cn(
                "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 font-medium text-xs transition-all border border-transparent",
                style,
                className
            )}
        >
            <Icon className={cn("h-3.5 w-3.5", iconClass)} />
            <span className="whitespace-nowrap">{label}</span>
        </div>
    );
};
