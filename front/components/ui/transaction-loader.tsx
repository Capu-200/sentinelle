"use client";

import { useFormStatus } from "react-dom";
import { CopyCheck, ShieldCheck, BrainCircuit, Lock, Server } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export function TransactionLoader() {
    const { pending } = useFormStatus();

    // Only mount/render if pending
    if (!pending) return null;

    return (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-background/80 backdrop-blur-md rounded-xl p-6 text-center animate-in fade-in duration-500">
            {/* Minimal Pulse Animation */}
            <div className="relative mb-6">
                <div className="absolute inset-0 bg-indigo-500/20 rounded-full animate-ping [animation-duration:1.5s]" />
                <div className="relative h-16 w-16 bg-background rounded-full border-2 border-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                    <ShieldCheck className="h-8 w-8 text-indigo-500 animate-pulse" />
                </div>
            </div>

            <h3 className="text-lg font-semibold text-foreground tracking-tight">
                Vérification Payon
            </h3>

            <p className="text-sm text-muted-foreground mt-1">
                Analyse de sécurité en cours...
            </p>

            {/* Subtle Progress Bar */}
            <div className="mt-6 h-1 w-24 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500 animate-[progress_1.5s_ease-in-out_infinite]" style={{ width: '100%' }} />
            </div>

            {/* Custom Keyframe for the progress bar (handled via Tailwind config usually, but here relies on generic pulse or custom class if available. I'll stick to a simple ping/pulse for now which always works) */}
        </div>
    );
}
