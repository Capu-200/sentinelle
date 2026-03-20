'use client';

import { useActionState, useEffect } from 'react';
import { useFormStatus } from 'react-dom';
import Link from 'next/link';
import { GlassCard } from '@/components/ui/glass-card';
import { Mail, ArrowLeft, Loader2, ArrowRight, CheckCircle } from 'lucide-react';
import { forgotPasswordAction, AuthActionState } from '@/app/actions/auth';

const initialState: AuthActionState = { error: '', success: false, message: '' };

function SubmitButton() {
    const { pending } = useFormStatus();
    return (
        <button
            type="submit"
            disabled={pending}
            className="group flex w-full items-center justify-center gap-2 rounded-2xl bg-indigo-600 hover:bg-indigo-700 py-4 font-bold text-white shadow-xl shadow-indigo-500/20 transition-all active:scale-95 disabled:opacity-70"
        >
            {pending ? <Loader2 className="h-5 w-5 animate-spin" /> : (
                <><span>Envoyer le lien</span><ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" /></>
            )}
        </button>
    );
}

export default function ForgotPasswordPage() {
    const [state, dispatch] = useActionState(forgotPasswordAction, initialState);

    return (
        <div className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-slate-950 to-indigo-950">
            <div className="w-full max-w-md space-y-6">
                <Link href="/login" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" /> Retour à la connexion
                </Link>

                <GlassCard className="p-8 space-y-6">
                    <div>
                        <h1 className="text-2xl font-black text-white">Mot de passe oublié ?</h1>
                        <p className="text-slate-400 text-sm mt-1">Entrez votre email pour recevoir un lien de réinitialisation.</p>
                    </div>

                    {state.success ? (
                        <div className="flex flex-col items-center gap-4 py-6 text-center">
                            <div className="h-16 w-16 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                                <CheckCircle className="h-8 w-8 text-emerald-400" />
                            </div>
                            <div>
                                <p className="font-bold text-white">Lien généré !</p>
                                {state.message && state.message.startsWith('http') ? (
                                    <Link href={state.message} className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 transition-colors">
                                        Réinitialiser mon mot de passe <ArrowRight className="h-4 w-4" />
                                    </Link>
                                ) : (
                                    <p className="text-slate-400 text-sm mt-1">{state.message}</p>
                                )}
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
                                    placeholder="votre@email.com"
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
            </div>
        </div>
    );
}
