"use client";

import { useState } from "react";
import { MessageSquarePlus, X, Check } from "lucide-react";
import { updateTransactionCommentAction } from "@/app/actions/transactions";
import { cn } from "@/lib/utils";

interface Props {
    transactionId: string;
    currentComment?: string;
    onSuccess?: () => void;
}

export const AddCommentButton = ({ transactionId, currentComment, onSuccess }: Props) => {
    const [isOpen, setIsOpen] = useState(false);
    const [comment, setComment] = useState(currentComment || "");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsSubmitting(true);

        try {
            const result = await updateTransactionCommentAction(transactionId, comment);

            if (result.success) {
                setIsOpen(false);
                onSuccess?.();
            } else {
                setError(result.message);
            }
        } catch (err) {
            setError("Une erreur est survenue");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <>
            {/* Trigger Button */}
            <button
                onClick={() => setIsOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                title={currentComment ? "Modifier le commentaire" : "Ajouter un commentaire"}
            >
                <MessageSquarePlus className="h-3.5 w-3.5" />
                <span>{currentComment ? "Modifier" : "Ajouter"} note</span>
            </button>

            {/* Modal Overlay */}
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in">
                    <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-in zoom-in-95 slide-in-from-bottom-4">
                        {/* Header */}
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-foreground">
                                {currentComment ? "Modifier" : "Ajouter"} un commentaire
                            </h3>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>

                        {/* Form */}
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label htmlFor="comment-input" className="text-sm font-medium text-muted-foreground mb-2 block">
                                    Votre note personnelle
                                </label>
                                <textarea
                                    id="comment-input"
                                    value={comment}
                                    onChange={(e) => setComment(e.target.value)}
                                    placeholder="Ex: Remboursement dîner, Cadeau anniversaire..."
                                    rows={4}
                                    maxLength={500}
                                    className="w-full rounded-xl border-0 bg-slate-100 px-4 py-3 text-sm outline-none ring-1 ring-transparent focus:bg-white focus:ring-primary/20 transition-all dark:bg-slate-800 dark:focus:bg-slate-900 text-slate-900 dark:text-white placeholder:text-slate-400 resize-none"
                                    autoFocus
                                />
                                <p className="text-xs text-muted-foreground mt-1 text-right">
                                    {comment.length}/500 caractères
                                </p>
                            </div>

                            {/* Error Message */}
                            {error && (
                                <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl text-sm">
                                    {error}
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => setIsOpen(false)}
                                    className="flex-1 px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-foreground font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                                >
                                    Annuler
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSubmitting || comment.trim().length === 0}
                                    className={cn(
                                        "flex-1 px-4 py-3 rounded-xl bg-primary text-primary-foreground font-medium transition-all flex items-center justify-center gap-2",
                                        (isSubmitting || comment.trim().length === 0) && "opacity-50 cursor-not-allowed"
                                    )}
                                >
                                    {isSubmitting ? (
                                        <span className="animate-pulse">Enregistrement...</span>
                                    ) : (
                                        <>
                                            <Check className="h-4 w-4" />
                                            <span>Enregistrer</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    );
};
