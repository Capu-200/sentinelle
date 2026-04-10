'use client';

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { AlertTriangle, Trash2, Loader2, X } from "lucide-react";
import { deleteAccountAction } from "@/app/actions/auth";

export const DeleteAccountButton = () => {
    const [isConfirming, setIsConfirming] = useState(false);
    const [isPending, startTransition] = useTransition();
    const router = useRouter();

    const handleDelete = () => {
        startTransition(async () => {
            // 1. Appel du backend pour archivage légal + suppression des cookies locaux
            await deleteAccountAction();
            
            // 2. Message de transparence RGPD vs LCB-FT
            toast.custom((t) => (
                <div className={`${t.visible ? 'animate-enter' : 'animate-leave'} max-w-md w-full bg-slate-900 border border-slate-700 shadow-2xl rounded-2xl pointer-events-auto flex ring-1 ring-black ring-opacity-5`}>
                    <div className="flex-1 w-0 p-4">
                        <div className="flex items-start">
                            <div className="flex-shrink-0 pt-0.5">
                                <AlertTriangle className="h-10 w-10 text-amber-500" />
                            </div>
                            <div className="ml-3 flex-1">
                                <p className="text-sm font-bold text-white uppercase tracking-wider">
                                    Compte désactivé
                                </p>
                                <p className="mt-1 text-xs text-slate-300 leading-relaxed font-medium">
                                    Vos préférences ont été effacées. Conformément à la réglementation <span className="font-bold text-white">LCB-FT</span> sur la sécurité financière, vos données KYC et votre historique de transactions ont été <span className="text-amber-400 font-bold">archivés hermétiquement</span> pour la durée légale de 5 ans.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            ), { duration: 8000, position: 'bottom-center' });

            // 3. Redirection au login après lecture
            setTimeout(() => {
                router.push("/login");
            }, 6000);
        });
    };

    if (isConfirming) {
        return (
            <div className="w-full space-y-3 p-4 border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 rounded-xl">
                <p className="text-sm font-bold text-red-600 dark:text-red-400">
                    Êtes-vous sûr de vouloir supprimer ce compte ?
                </p>
                <p className="text-xs text-red-500/80 dark:text-red-400/80">
                    L'accès sera immédiatement révoqué.
                </p>
                <div className="flex gap-2 pt-2">
                    <button 
                        onClick={handleDelete}
                        disabled={isPending}
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold text-xs transition-all disabled:opacity-50"
                    >
                        {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                        {isPending ? "Archivage..." : "Oui, supprimer"}
                    </button>
                    <button 
                        onClick={() => setIsConfirming(false)}
                        disabled={isPending}
                         className="flex items-center justify-center py-2.5 px-4 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 active:scale-95 font-bold text-xs transition-all disabled:opacity-50"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
            </div>
        );
    }

    return (
        <button 
            type="button"
            onClick={() => setIsConfirming(true)}
            className="w-full flex justify-between items-center px-4 py-3.5 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 hover:border-red-200 hover:bg-red-50 dark:hover:border-red-900/50 dark:hover:bg-red-950/20 hover:text-red-600 dark:hover:text-red-400 transition-colors group"
        >
            <span className="text-sm font-semibold">Supprimer mon compte RGPD</span>
            <Trash2 className="h-4 w-4 opacity-70 group-hover:opacity-100" />
        </button>
    );
};
