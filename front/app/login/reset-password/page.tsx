'use client';

import { useActionState, useState, Suspense } from 'react';
import { useFormStatus } from 'react-dom';
import { useRouter, useSearchParams } from 'next/navigation';
import { GlassCard } from '@/components/ui/glass-card';
import { Eye, EyeOff, Lock, Mail, ArrowLeft, Loader2, CheckCircle } from 'lucide-react';
import Link from 'next/link';
import { resetPasswordAction, AuthActionState } from '@/app/actions/auth';

const initialState: AuthActionState = { error: '', success: false, message: '' };

function SubmitButton() {
    const { pending } = useFormStatus();
    return (
        <button
            type="submit"
            disabled={pending}
            className="group flex w-full items-center justify-center gap-2 rounded-2xl bg-indigo-600 hover:bg-indigo-700 py-4 font-bold text-white shadow-xl shadow-indigo-500/20 transition-all active:scale-95 disabled:opacity-70"
        >
            {pending ? <Loader2 className="h-5 w-5 animate-spin" /> : <span>Mettre à jour le mot de passe</span>}
        </button>
    );
}

function ResetPasswordForm() {
    const searchParams = useSearchParams();
    const prefillEmail = searchParams.get('email') || '';
    const router = useRouter();
    const [state, dispatch] = useActionState(resetPasswordAction, initialState);
    const [showPwd, setShowPwd] = useState(false);

    if (state.success) {
        setTimeout(() => router.push('/login'), 3000);
    }

    return (
        <GlassCard className="p-8 space-y-6">
            <div>
                <h1 className="text-2xl font-black text-white">Nouveau mot de passe</h1>
                <p className="text-slate-400 text-sm mt-1">Choisissez un mot de passe sécurisé (6 caractères minimum).</p>
            </div>

            {state.success ? (
                <div className="flex flex-col items-center gap-4 py-6 text-center">
                    <div className="h-16 w-16 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                        <CheckCircle className="h-8 w-8 text-emerald-400" />
                    </div>
                    <div>
                        <p className="font-bold text-white">{state.message}</p>
                        <p className="text-slate-400 text-sm mt-1">Redirection automatique vers la connexion...</p>
                    </div>
                </div>
            ) : (
                <form action={dispatch} className="space-y-4">
                    <div className="relative">
                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                        <input
                            name="email"
                            type="email"
                            required
                            defaultValue={prefillEmail}
                            placeholder="votre@email.com"
                            className="w-full rounded-xl bg-slate-800/60 pl-12 pr-4 py-4 text-white placeholder:text-slate-500 outline-none ring-1 ring-slate-700 focus:ring-indigo-500 transition-all"
                        />
                    </div>

                    <div className="relative">
                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                        <input
                            name="password"
                            type={showPwd ? 'text' : 'password'}
                            required
                            placeholder="Nouveau mot de passe"
                            className="w-full rounded-xl bg-slate-800/60 pl-12 pr-12 py-4 text-white placeholder:text-slate-500 outline-none ring-1 ring-slate-700 focus:ring-indigo-500 transition-all"
                        />
                        <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors">
                            {showPwd ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                        </button>
                    </div>

                    <div className="relative">
                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                        <input
                            name="confirm"
                            type={showPwd ? 'text' : 'password'}
                            required
                            placeholder="Confirmer le mot de passe"
                            className="w-full rounded-xl bg-slate-800/60 pl-12 pr-4 py-4 text-white placeholder:text-slate-500 outline-none ring-1 ring-slate-700 focus:ring-indigo-500 transition-all"
                        />
                    </div>

                    {state.error && (
                        <p className="text-sm text-red-400 bg-red-500/10 px-4 py-3 rounded-xl border border-red-500/20">
                            {state.error}
                        </p>
                    )}

                    <SubmitButton />
                </form>
            )}
        </GlassCard>
    );
}

export default function ResetPasswordPage() {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-slate-950 to-indigo-950">
            <div className="w-full max-w-md space-y-6">
                <Link href="/login" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" /> Retour à la connexion
                </Link>
                <Suspense fallback={<div className="h-64 rounded-3xl bg-slate-800/40 animate-pulse" />}>
                    <ResetPasswordForm />
                </Suspense>
            </div>
        </div>
    );
}
