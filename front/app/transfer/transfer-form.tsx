"use client";

import { createTransferAction } from "@/app/actions";
import { getContactsAction } from "@/app/actions/contacts"; // Import the new action
import { Send, RefreshCw, ShieldCheck } from "lucide-react";
import { useActionState, useState, useEffect } from "react"; // Added useActionState
import { useFormStatus } from "react-dom";
import { cn } from "@/lib/utils";
import { useSearchParams } from "next/navigation";
import { TransactionLoader } from "@/components/ui/transaction-loader";

interface Contact {
    contact_id: string;
    name: string;
    email?: string;
    iban?: string;
    initials: string;
    is_internal: boolean;
}

interface Props {
    contacts: Contact[]; // Still accept initial props
}

function SubmitButton() {
    const { pending } = useFormStatus();

    return (
        <button
            type="submit"
            disabled={pending}
            className={cn(
                "group mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-primary py-4 font-bold text-primary-foreground shadow-xl transition-all active:scale-95 disabled:opacity-70 disabled:active:scale-100",
                pending && "cursor-not-allowed opacity-80"
            )}
        >
            {pending ? (
                <span className="animate-pulse">Envoi en cours...</span>
            ) : (
                <>
                    <span>Confirmer l'envoi</span>
                    <Send className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </>
            )}
        </button>
    );
}

export function TransferForm({ contacts: initialContacts }: Props) {
    const searchParams = useSearchParams();
    const initialRecipient = searchParams.get("to") || "";

    // Initial state for the form action
    const initialState = {
        success: false,
        message: "",
    };

    // Use useActionState instead of useFormState
    // @ts-ignore
    const [state, formAction] = useActionState(createTransferAction, initialState);

    const [contacts, setContacts] = useState<Contact[]>(initialContacts);
    const [amount, setAmount] = useState("");
    const [recipient, setRecipient] = useState(initialRecipient);
    const [isLoading, setIsLoading] = useState(false);
    const [errorDismissed, setErrorDismissed] = useState(false); // Moved state up

    // Fetch contacts on mount if empty (Client-Side Fallback)
    useEffect(() => {
        const fetchContacts = async () => {
            if (contacts.length === 0) {
                setIsLoading(true);
                try {
                    const data = await getContactsAction();
                    if (data) setContacts(data);
                } catch (error) {
                    console.error("Failed to fetch contacts client-side", error);
                } finally {
                    setIsLoading(false);
                }
            }
        };
        fetchContacts();
    }, [contacts.length]);

    // Filter valid contacts (those with email or iban)
    const validContacts = contacts.filter(c => c.email || c.iban);

    // Auto-select contact logic if `initialRecipient` matches a contact ID or email
    useEffect(() => {
        if (initialRecipient && contacts.length > 0) {
            const matched = contacts.find(c => c.contact_id === initialRecipient || c.email === initialRecipient);
            if (matched) {
                setRecipient(matched.email || matched.iban || "");
            } else if (initialRecipient.includes("@") || initialRecipient.startsWith("FR")) {
                // Even if not matched, if param looks like email/iban, set it
                setRecipient(initialRecipient);
            }
        }
    }, [initialRecipient, contacts]);

    // Reset dismissed state when submitting again
    useEffect(() => {
        if (state?.message) {
            setErrorDismissed(false); // New error arrived, show screen
        }
    }, [state]);

    const handleContactClick = (contact: Contact) => {
        setRecipient(contact.email || contact.iban || "");
    };

    // If we have a fresh server error and haven't dismissed it, show BLOCK SCREEN
    if (state?.message && !state.success && !errorDismissed) {
        return (
            <div className="flex flex-1 flex-col items-center justify-center p-6 text-center animate-in zoom-in-95 duration-300">
                <div className="mb-6 relative">
                    <div className="absolute inset-0 bg-red-500/10 blur-2xl rounded-full" />
                    <div className="relative h-20 w-20 bg-red-50 dark:bg-red-900/20 rounded-full flex items-center justify-center border-2 border-red-100 dark:border-red-900">
                        <ShieldCheck className="h-10 w-10 text-red-500" />
                    </div>
                </div>

                <h2 className="text-xl font-bold text-red-600 dark:text-red-500 mb-2">
                    Transaction Refusée
                </h2>

                <p className="text-muted-foreground max-w-xs mb-8">
                    {state.message}
                </p>

                <button
                    onClick={() => setErrorDismissed(true)}
                    className="w-full max-w-xs py-3 px-4 rounded-xl bg-slate-100 dark:bg-slate-800 text-foreground font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                >
                    Modifier la transaction
                </button>
            </div>
        );
    }

    return (
        <form action={formAction} className="relative flex flex-1 flex-col h-full">
            <TransactionLoader />
            {/* ... Form Content ... */}
            <div className="space-y-4 pt-4">
                <label className="text-sm font-medium text-muted-foreground ml-1">Pour qui ?</label>

                {/* Quick Access List */}
                {isLoading ? (
                    <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide opacity-50">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-10 w-24 bg-slate-100 rounded-full animate-pulse" />
                        ))}
                    </div>
                ) : validContacts.length > 0 ? (
                    <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
                        {validContacts.map((c) => (
                            <div
                                key={c.contact_id}
                                onClick={() => handleContactClick(c)}
                                className={cn(
                                    "flex flex-shrink-0 items-center gap-2 rounded-full border bg-white p-1 pr-4 shadow-sm cursor-pointer transition-all dark:bg-slate-900 dark:border-slate-800",
                                    (recipient === c.email || recipient === c.iban)
                                        ? "border-indigo-600 ring-2 ring-indigo-100 dark:ring-indigo-900"
                                        : "border-slate-200 hover:border-indigo-300"
                                )}
                            >
                                <div className={cn(
                                    "h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold",
                                    c.is_internal ? "bg-indigo-100 text-indigo-600" : "bg-slate-100 text-slate-600"
                                )}>
                                    {c.initials}
                                </div>
                                <span className="text-sm font-medium">{c.name}</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-xs text-muted-foreground italic ml-1">Aucun contact enregistré.</p>
                )}

                <div className="relative">
                    <input
                        required
                        name="recipient"
                        type="text"
                        placeholder="Email ou ID utilisateur..."
                        value={recipient}
                        onChange={(e) => setRecipient(e.target.value)}
                        className="w-full rounded-xl border-0 bg-slate-100 px-4 py-4 text-base outline-none ring-1 ring-transparent focus:bg-white focus:ring-primary/20 transition-all dark:bg-slate-800 dark:focus:bg-slate-900 text-slate-900 dark:text-white placeholder:text-slate-400"
                    />
                    {/* Status Indicator inside input */}
                    {recipient && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                            {contacts.find(c => c.email === recipient) ? (
                                <span className="text-[10px] bg-green-100 text-green-600 px-2 py-1 rounded-full font-bold">Contact</span>
                            ) : (
                                null
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Comment Field (Optional) */}
            <div className="space-y-2">
                <label htmlFor="comment" className="text-sm font-medium text-muted-foreground ml-1">Commentaire (optionnel)</label>
                <textarea
                    name="comment"
                    id="comment"
                    rows={2}
                    placeholder="Ajoutez une note à cette transaction..."
                    className="w-full rounded-xl border-0 bg-slate-100 px-4 py-3 text-sm outline-none ring-1 ring-transparent focus:bg-white focus:ring-primary/20 transition-all dark:bg-slate-800 dark:focus:bg-slate-900 text-slate-900 dark:text-white placeholder:text-slate-400 resize-none"
                />
            </div>

            {/* Giant Amount Input (Centered vertically) */}
            <div className="flex-1 flex flex-col items-center justify-center gap-4 min-h-[200px]">
                <label htmlFor="amount" className="text-sm font-medium text-muted-foreground uppercase tracking-widest">
                    Montant à envoyer
                </label>
                <div className="relative flex items-center justify-center w-full">
                    <input
                        required
                        name="amount"
                        id="amount"
                        type="text"
                        inputMode="decimal"
                        placeholder="0"
                        value={amount}
                        onChange={(e) => {
                            const val = e.target.value.replace(',', '.'); // Allow comma as decimal separator
                            if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                                setAmount(val);
                            }
                        }}
                        className="w-full text-center bg-transparent text-6xl md:text-8xl font-black tracking-tighter outline-none placeholder:text-slate-100 dark:placeholder:text-slate-800 text-slate-900 dark:text-white transition-all scale-100 focus:scale-105"
                        style={{ maxWidth: '400px' }}
                    />
                    <span className="text-5xl font-medium text-slate-400 absolute right-[10%] top-6 pointer-events-none">PYC</span>
                </div>
            </div>

            {/* Bottom Actions */}
            <div className="mt-auto pb-4 space-y-4">

                {/* Error Message Display */}
                {state?.message && !state.success && (
                    <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl flex items-center gap-2 text-sm font-medium animate-in fade-in slide-in-from-bottom-2 border border-red-100 dark:border-red-900">
                        <div className="h-5 w-5 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center shrink-0 font-bold">!</div>
                        {state.message}
                    </div>
                )}

                <div className="rounded-xl bg-slate-50 p-4 text-center text-xs text-muted-foreground dark:bg-slate-900">
                    Frais de transaction : <span className="font-bold text-foreground">Gratuit</span>
                </div>
                <SubmitButton />
            </div>
        </form>
    );
}
