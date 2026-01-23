"use client";

import { createTransferAction } from "@/app/actions";
import { ArrowLeft, Send } from "lucide-react";
import Link from "next/link";
import { useFormStatus } from "react-dom";
import { cn } from "@/lib/utils";
import { useState } from "react";

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

export default function TransferPage() {
    const [amount, setAmount] = useState("");

    const quickUsers = [
        { name: "Alice", avatar: "A", color: "bg-pink-100 text-pink-600 dark:bg-pink-900/40 dark:text-pink-400" },
        { name: "Bob", avatar: "B", color: "bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400" },
        { name: "Charlie", avatar: "C", color: "bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400" },
    ];

    return (
        <div className="flex min-h-[80vh] flex-col">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <Link href="/" className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                    <ArrowLeft className="h-6 w-6" />
                </Link>
                <h1 className="text-xl font-bold">Effectuer un virement</h1>
            </div>

            <form action={createTransferAction} className="flex flex-1 flex-col justify-between">
                <div className="space-y-8">

                    {/* Recipient Selection */}
                    <div className="space-y-4">
                        <label className="text-sm font-medium text-muted-foreground ml-1">Pour qui ?</label>

                        {/* Recent Pill List */}
                        <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
                            {quickUsers.map((u, i) => (
                                <div key={i} className="flex items-center gap-2 rounded-full border border-slate-200 bg-white p-1 pr-4 shadow-sm cursor-pointer hover:border-primary transition-colors dark:bg-slate-900 dark:border-slate-800">
                                    <div className={cn("h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold", u.color)}>
                                        {u.avatar}
                                    </div>
                                    <span className="text-sm font-medium">{u.name}</span>
                                </div>
                            ))}
                        </div>

                        <input
                            required
                            name="recipient"
                            type="text"
                            placeholder="Ou saisir un email / ID..."
                            className="w-full rounded-xl border-0 bg-slate-100 px-4 py-4 text-base outline-none ring-1 ring-transparent focus:bg-white focus:ring-primary/20 transition-all dark:bg-slate-800 dark:focus:bg-slate-900"
                        />
                    </div>

                    {/* Giant Amount Input */}
                    <div className="flex flex-col items-center justify-center py-8 gap-2">
                        <label htmlFor="amount" className="text-sm font-medium text-muted-foreground">
                            Montant à envoyer
                        </label>
                        <div className="relative flex items-center justify-center">
                            <input
                                required
                                name="amount"
                                id="amount"
                                type="text"
                                inputMode="decimal"
                                placeholder="0"
                                value={amount}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    if (val === '' || /^\d*\.?\d{0,2}$/.test(val)) {
                                        setAmount(val);
                                    }
                                }}
                                className="w-full text-center bg-transparent text-7xl font-bold tracking-tighter outline-none placeholder:text-slate-200 dark:placeholder:text-slate-800"
                                style={{ maxWidth: '300px' }} // constrain width to avoid scrolling
                            />
                            <span className="text-4xl font-medium text-muted-foreground absolute right-0 translate-x-full top-4">€</span>
                        </div>
                    </div>
                </div>

                {/* Bottom Actions */}
                <div className="mt-auto">
                    <div className="rounded-xl bg-slate-50 p-4 text-center text-xs text-muted-foreground dark:bg-slate-900">
                        Frais de transaction : <span className="font-bold text-foreground">Gratuit</span>
                    </div>
                    <SubmitButton />
                </div>
            </form>
        </div>
    );
}
