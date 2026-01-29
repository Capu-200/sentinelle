import { Transaction } from "@/types/transaction";
import { cn } from "@/lib/utils";
import { ArrowUpRight, ArrowDownLeft, MessageSquare } from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";
import { AddCommentButton } from "./add-comment-button";

interface Props {
    transaction: Transaction;
}

// Composant helper pour le drapeau
const CountryFlag = ({ code }: { code?: string }) => {
    if (!code) return <span className="text-lg leading-none">🌍</span>;

    // Fallback pour "EN" -> "GB" (Angleterre)
    const safeCode = code.toUpperCase() === 'EN' ? 'GB' : code;

    return (
        <img
            src={`https://flagcdn.com/24x18/${safeCode.toLowerCase()}.png`}
            srcSet={`https://flagcdn.com/48x36/${safeCode.toLowerCase()}.png 2x`}
            width="16"
            height="12"
            alt={code}
            className="inline-block object-contain rounded-sm shadow-sm opacity-90 hover:opacity-100 transition-opacity"
            style={{ verticalAlign: 'text-bottom' }}
        />
    );
};

export const TransactionItem = ({ transaction }: Props) => {
    const isIncoming = transaction.direction === 'INCOMING';
    const hasComment = transaction.comment && transaction.comment.trim().length > 0;

    // Affichage du trajet Pays-Pays
    const CountryRouteDisplay = () => {
        if (!transaction.sourceCountry) return null;
        return (
            <div className="flex items-center gap-1.5 px-1.5 py-0.5 rounded-md bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800/50">
                <CountryFlag code={transaction.sourceCountry} />
                <span className="text-slate-400 text-[10px] leading-none">→</span>
                <CountryFlag code={transaction.destinationCountry} />
            </div>
        );
    };

    return (
        <div className="flex flex-col gap-2 p-4 border rounded-xl bg-card hover:bg-accent/50 transition-colors">
            <div className="flex items-center justify-between">
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
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{new Date(transaction.date).toLocaleDateString()}</span>
                            <CountryRouteDisplay />
                        </div>
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

            {/* Commentaire utilisateur */}
            {hasComment && (
                <div className="flex items-start gap-2 mt-1 p-3 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800">
                    <MessageSquare className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-muted-foreground italic leading-relaxed flex-1">
                        {transaction.comment}
                    </p>
                </div>
            )}

            {/* Action Footer */}
            <div className="flex items-center justify-end pt-2 border-t border-slate-100 dark:border-slate-800">
                <AddCommentButton
                    transactionId={transaction.id}
                    currentComment={transaction.comment}
                />
            </div>
        </div>
    );
};
