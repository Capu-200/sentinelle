import { Transaction } from "@/types/transaction";
import { cn } from "@/lib/utils";
import { ArrowUpRight, ArrowDownLeft } from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";

interface Props {
    transaction: Transaction;
}

export const TransactionItem = ({ transaction }: Props) => {
    const isIncoming = transaction.direction === 'INCOMING';

    return (
        <div className="flex items-center justify-between p-4 border rounded-xl bg-card hover:bg-accent/50 transition-colors">
            <div className="flex items-center gap-4">
                <div className={cn(
                    "h-10 w-10 flex items-center justify-center rounded-full",
                    isIncoming ? "bg-green-100 dark:bg-green-900/30" : "bg-slate-100 dark:bg-slate-800"
                )}>
                    {isIncoming ? (
                        <ArrowDownLeft className="h-5 w-5 text-green-600 dark:text-green-400" />
                    ) : (
                        <ArrowUpRight className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                    )}
                </div>
                <div>
                    <p className="font-medium text-sm text-foreground">{transaction.recipient}</p>
                    <p className="text-xs text-muted-foreground">
                        {new Date(transaction.date).toLocaleDateString()}
                    </p>
                </div>
            </div>

            <div className="text-right">
                <p className={cn(
                    "font-bold text-sm",
                    isIncoming ? "text-green-600 dark:text-green-400" : "text-foreground"
                )}>
                    {isIncoming ? "+" : "-"} {transaction.amount.toLocaleString()} PYC
                </p>
                <div className="mt-1">
                    <StatusBadge status={transaction.status} className="px-2 py-0.5 text-[10px]" />
                </div>
            </div>
        </div>
    );
};
