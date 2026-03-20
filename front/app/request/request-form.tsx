"use client";

import { createRequestAction } from "@/app/actions/request";
import { getContactsAction } from "@/app/actions/contacts";
import { HandCoins, ShieldCheck } from "lucide-react";
import { useActionState, useState, useEffect } from "react";
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
    contacts: Contact[];
    currentUserEmail?: string;
    currentUserName?: string;
}

function SubmitButton() {
    const { pending } = useFormStatus();

    return (
        <button
            type="submit"
            disabled={pending}
            className={cn(
                "group mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-indigo-600 hover:bg-indigo-700 py-4 font-bold text-white shadow-xl shadow-indigo-500/20 transition-all active:scale-95 disabled:opacity-70 disabled:active:scale-100",
                pending && "cursor-not-allowed opacity-80"
            )}
        >
            {pending ? (
                <span className="animate-pulse">Demande en cours...</span>
            ) : (
                <>
                    <span>Demander les fonds</span>
                    <HandCoins className="h-4 w-4 transition-transform group-hover:scale-110" />
                </>
            )}
        </button>
    );
}

export function RequestForm({ contacts: initialContacts, currentUserEmail, currentUserName }: Props) {
    const searchParams = useSearchParams();
    const initialRecipient = searchParams.get("to") || "";

    const initialState = {
        success: false,
        message: "",
    };

    // @ts-ignore
    const [state, formAction] = useActionState(createRequestAction, initialState);

    const [contacts, setContacts] = useState<Contact[]>(initialContacts);
    const [amount, setAmount] = useState("");
    const [recipient, setRecipient] = useState(initialRecipient);
    const [isLoading, setIsLoading] = useState(false);
    const [errorDismissed, setErrorDismissed] = useState(false);

    useEffect(() => {
        const fetchContacts = async () => {
            if (contacts.length === 0) {
                setIsLoading(true);
                try {
                    const data = await getContactsAction();
                    if (data) setContacts(data);
                } catch (error) {
                    console.error("Failed to fetch contacts", error);
                } finally {
                    setIsLoading(false);
                }
            }
        };
        fetchContacts();
    }, [contacts.length]);

    const validContacts = contacts.filter(c => c.email || c.iban);

    useEffect(() => {
        if (initialRecipient && contacts.length > 0) {
            const matched = contacts.find(c => c.contact_id === initialRecipient || c.email === initialRecipient);
            if (matched) {
                setRecipient(matched.email || matched.iban || "");
            } else if (initialRecipient.includes("@") || initialRecipient.startsWith("FR")) {
                setRecipient(initialRecipient);
            }
        }
    }, [initialRecipient, contacts]);

    useEffect(() => {
        if (state?.message) {
            setErrorDismissed(false);
        }
    }, [state]);

    const handleContactClick = (contact: Contact) => {
        setRecipient(contact.email || contact.iban || "");
    };

    if (state?.message && !state.success && !errorDismissed) {
        return (
            <div className="flex flex-1 flex-col items-center justify-center p-6 text-center animate-in zoom-in-95 duration-300">
                <div className="mb-6 relative">
                    <div className="absolute inset-0 bg-red-500/10 blur-2xl rounded-full" />
                    <div className="relative h-20 w-20 bg-red-50 dark:bg-red-900/20 rounded-full flex items-center justify-center border-2 border-red-100 dark:border-red-900">
                        <ShieldCheck className="h-10 w-10 text-red-500" />
                    </div>
                </div>
                <h2 className="text-xl font-bold text-red-600 dark:text-red-500 mb-2">Refusé</h2>
                <p className="text-muted-foreground max-w-xs mb-8">{state.message}</p>
                <button
                    onClick={() => setErrorDismissed(true)}
                    className="w-full max-w-xs py-3 px-4 rounded-xl bg-slate-100 dark:bg-slate-800 text-foreground font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                >
                    Modifier la demande
                </button>
            </div>
        );
    }

    return (
        <form action={formAction} className="relative flex flex-1 flex-col h-full">
            <TransactionLoader />
            <div className="space-y-4 pt-4">
                <label className="text-sm font-medium text-muted-foreground ml-1">À qui ?</label>
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
                    <input type="hidden" name="knownContacts" value={contacts.map(c => c.email + "|" + c.iban).join(',')} />
                    <input type="hidden" name="fromUser" value={currentUserEmail || ""} />
                    <input type="hidden" name="fromUserName" value={currentUserName || currentUserEmail?.split('@')[0] || ""} />
                    <input
                        required
                        name="recipient"
                        type="text"
                        placeholder="Email ou ID utilisateur..."
                        value={recipient}
                        onChange={(e) => setRecipient(e.target.value)}
                        className="w-full rounded-xl border-0 bg-slate-100 px-4 py-4 text-base outline-none ring-1 ring-transparent focus:bg-white focus:ring-primary/20 transition-all dark:bg-slate-800 dark:focus:bg-slate-900 text-slate-900 dark:text-white placeholder:text-slate-400"
                    />
                </div>
            </div>

            <div className="space-y-2 mt-4">
                <label htmlFor="comment" className="text-sm font-medium text-muted-foreground ml-1">Motif (optionnel)</label>
                <textarea
                    name="comment"
                    id="comment"
                    rows={2}
                    placeholder="Pour le restaurant d'hier..."
                    className="w-full rounded-xl border-0 bg-slate-100 px-4 py-3 text-sm outline-none ring-1 ring-transparent focus:bg-white focus:ring-primary/20 transition-all dark:bg-slate-800 dark:focus:bg-slate-900 text-slate-900 dark:text-white placeholder:text-slate-400 resize-none"
                />
            </div>

            <div className="flex-1 flex flex-col items-center justify-center gap-4 min-h-[200px]">
                <label htmlFor="amount" className="text-sm font-medium text-muted-foreground uppercase tracking-widest">
                    Montant demandé
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
                            const val = e.target.value.replace(',', '.');
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

            <div className="mt-auto pb-4 space-y-4">
                {state?.message && !state.success && (
                    <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl flex items-center gap-2 text-sm font-medium animate-in fade-in slide-in-from-bottom-2 border border-red-100 dark:border-red-900">
                        <div className="h-5 w-5 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center shrink-0 font-bold">!</div>
                        {state.message}
                    </div>
                )}
                <SubmitButton />
            </div>
        </form>
    );
}
