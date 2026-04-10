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

const REASON_TRANSLATIONS: Record<string, string> = {
    "RULE_MAX_AMOUNT": "Montant supérieur à la limite autorisée",
    "RULE_INSUFFICIENT_FUNDS": "Solde insuffisant",
    "RULE_ACCOUNT_LOCKED": "Compte ou portefeuille bloqué",
    "RULE_SELF_TRANSFER": "Virement vers soi-même interdit",
    "RULE_INVALID_AMOUNT": "Montant invalide",
    "RULE_COUNTRY_BLOCKED": "Destination non autorisée",
    "RULE_DESTINATION_LOCKED": "Le portefeuille cible est bloqué",
    "RULE_AMOUNT_ANOMALY": "Montant très inhabituel pour vos habitudes",
    "RULE_FREQ_SPIKE": "Pic d'activité (trop de virements successifs)",
    "RULE_NEW_ACCOUNT_ACTIVITY": "Activité suspecte (nouveau compte)",
    "RULE_NEW_BENEFICIARY": "Montant trop élevé vers un inconnu",
    "RULE_GEO_ANOMALY": "Localisation ou trajet inhabituel",
    "RULE_ODD_HOUR": "Virement nocturne suspect",
    "RULE_HIGH_RISK_PROFILE": "Profil à risque nécessitant contrôle",
    "RULE_RECIDIVISM": "Activité récidiviste suspecte",
    "RULE_CIRCULAR_FLOW": "Mouvement de fonds circulaire détecté",
    "ML_BLOCK": "Confiance très faible estimée par l'IA",
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
        <div className="flex flex-col gap-2 p-4 border border-slate-100 dark:border-slate-800 rounded-xl bg-slate-950 hover:bg-slate-900 transition-colors">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className={cn(
                        "h-10 w-10 flex-shrink-0 flex items-center justify-center rounded-full",
                        isIncoming ? "bg-green-100 dark:bg-green-900/30" : "bg-slate-100 dark:bg-slate-800"
                    )}>
                        {isIncoming ? (
                            <ArrowDownLeft className="h-5 w-5 text-green-600 dark:text-green-400" />
                        ) : (
                            <ArrowUpRight className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                        )}
                    </div>
                    <div className="min-w-0 flex-1 pr-2">
                        <div className="flex items-center gap-1.5 font-medium text-sm text-foreground truncate" title={transaction.recipient}>
                            {isIncoming ? (
                                <>
                                    <span className="truncate max-w-[120px] md:max-w-xs">{transaction.recipient}</span>
                                    <span className="text-slate-500 font-normal">→</span>
                                    <span className="font-bold text-indigo-400 dark:text-indigo-300">Moi</span>
                                </>
                            ) : (
                                <>
                                    <span className="font-bold text-indigo-400 dark:text-indigo-300">Moi</span>
                                    <span className="text-slate-500 font-normal">→</span>
                                    <span className="truncate max-w-[120px] md:max-w-xs">{transaction.recipient}</span>
                                </>
                            )}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                            <span className="flex-shrink-0">
                                {new Date(transaction.date).toLocaleDateString('fr-FR')} à {new Date(transaction.date).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                            <CountryRouteDisplay />
                        </div>
                    </div>
                </div>

                <div className="text-right flex-shrink-0">
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

            {/* Raisons d'alerte / blocage IA */}
            {transaction.reasons && transaction.reasons.length > 0 && (() => {
                const isDefinitive = ['REJECTED', 'BLOCK'].includes(transaction.status);
                const isWarning = ['REVIEW', 'SUSPECT'].includes(transaction.status);
                if (!isDefinitive && !isWarning) return null;

                const alertStyle = isDefinitive
                    ? "bg-red-50 dark:bg-red-950/30 border-red-100 dark:border-red-900/50 text-red-600 dark:text-red-400"
                    : "bg-amber-50 dark:bg-amber-950/30 border-amber-100 dark:border-amber-900/50 text-amber-600 dark:text-amber-400";
                const textStyle = isDefinitive
                    ? "text-red-700 dark:text-red-300"
                    : "text-amber-700 dark:text-amber-300";
                const label = isDefinitive ? "Transaction bloquée" : "Avertissement";

                return (
                    <div className={`flex flex-col gap-1 mt-1 p-3 rounded-lg border ${alertStyle}`}>
                        <div className="flex items-center gap-1.5 mb-1">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg>
                            <span className="text-[10px] font-bold uppercase tracking-wider">{label}</span>
                        </div>
                        {transaction.reasons.map((reason, idx) => (
                            <p key={idx} className={`text-xs font-medium leading-relaxed ${textStyle}`}>
                                • {REASON_TRANSLATIONS[reason] || reason.replace("RULE_", "").replace(/_/g, " ")}
                            </p>
                        ))}
                    </div>
                );
            })()}

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
