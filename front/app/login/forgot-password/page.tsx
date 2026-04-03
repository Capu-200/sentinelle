'use client';

import { useActionState, useEffect } from 'react';
import { useFormStatus } from 'react-dom';
import Link from 'next/link';

import { forgotPasswordAction, AuthActionState } from '@/app/actions/auth';
import toast from 'react-hot-toast';

const initialState: AuthActionState = { error: '', success: false, message: '' };

function SubmitButton() {
    const { pending } = useFormStatus();
    return (
        <button
            type="submit"
            disabled={pending}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold shadow-lg shadow-indigo-500/25 active:scale-[0.98] transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
        >
            {pending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
                <>
                    Réinitialiser
                    <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </>
            )}
        </button>
    );
}

export default function ForgotPasswordPage() {
    const [state, dispatch] = useActionState(forgotPasswordAction, initialState);

    useEffect(() => {
        if (state?.error) toast.error(state.error);
        if (state?.success) toast.success(state.message || 'Email envoyé !');
    }, [state]);

    return (
        <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
            <div className="absolute inset-0 bg-slate-50 dark:bg-slate-950 -z-20" />
            <div className="absolute top-1/4 -left-20 w-96 h-96 bg-indigo-500/20 rounded-full blur-[100px] -z-10" />
            <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-purple-500/20 rounded-full blur-[100px] -z-10" />

            <div className="w-full max-w-md">
                <div className="mb-6">
                    <Link href="/login" className="inline-flex items-center gap-2 text-slate-500 hover:text-indigo-600 transition-colors font-medium text-sm group">
                        <ArrowLeft className="h-4 w-4 group-hover:-translate-x-1 transition-transform" />
                        Retour à la connexion
                    </Link>
                </div>

                <div className="text-center mb-8">
                    <h1 className="text-3xl font-black bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 mb-2">
                        Mot de passe oublié
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400">
                        Entrez votre email pour réinitialiser votre accès
                    </p>
                </div>

                <GlassCard className="p-8 backdrop-blur-xl border-white/20 dark:border-white/10 shadow-2xl">
                    {state.success ? (
                        <div className="flex flex-col items-center gap-4 py-4 text-center">
                            <div className="h-16 w-16 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                                <CheckCircle className="h-8 w-8 text-emerald-400" />
                            </div>
                            <div>
                                <p className="font-bold text-slate-900 dark:text-white">Lien généré !</p>
                                {state.message && state.message.startsWith('http') ? (
                                    <Link href={state.message} className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 transition-colors">
                                        Réinitialiser mon mot de passe <ArrowRight className="h-4 w-4" />
                                    </Link>
                                ) : (
                                    <>
                                        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">{state.message}</p>
                                        <Link href="/login/reset-password" className="mt-3 inline-flex text-indigo-600 dark:text-indigo-400 font-bold hover:underline underline-offset-4 text-sm">
                                            Aller à la page de reset →
                                        </Link>
                                    </>
                                )}
                            </div>
                        </div>
                    ) : (
                        <form action={dispatch} className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold ml-1 text-slate-700 dark:text-slate-300">Email du compte</label>
                                <div className="relative group">
                                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                                    <input
                                        name="email"
                                        type="email"
                                        required
                                        placeholder="jacques@payon.app"
                                        className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-medium placeholder:text-slate-400 text-slate-900 dark:text-white"
                                    />
                                </div>
                            </div>

                            {state.error && (
                                <p className="p-3 text-red-500 text-xs font-semibold text-center bg-red-500/10 rounded-lg border border-red-500/20">
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
