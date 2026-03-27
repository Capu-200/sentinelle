'use client';

import { useActionState, useEffect, useState } from 'react';
import { useFormStatus } from 'react-dom';
import { useRouter } from 'next/navigation';
import { GlassCard } from '@/components/ui/glass-card';
import { Eye, EyeOff, Lock, Mail, ArrowRight, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { resetPasswordAction, type ResetPasswordState } from '../../actions/auth';
import toast from 'react-hot-toast';

const initialState: ResetPasswordState = {
    error: '',
    success: false,
    message: '',
};

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
                    Changer le mot de passe
                    <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </>
            )}
        </button>
    );
}

export default function ResetPasswordPage() {
    const router = useRouter();
    const [state, dispatch] = useActionState(resetPasswordAction, initialState);
    const [showPassword, setShowPassword] = useState(false);

    useEffect(() => {
        if (state?.error) {
            toast.error(state.error);
        }
        if (state?.success) {
            toast.success(state.message || 'Succès !');
            setTimeout(() => router.push('/login'), 2000);
        }
    }, [state, router]);

    return (
        <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-full bg-slate-50 dark:bg-slate-950 -z-20" />
            <div className="absolute top-1/4 -left-20 w-96 h-96 bg-indigo-500/20 rounded-full blur-[100px] -z-10" />
            <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-purple-500/20 rounded-full blur-[100px] -z-10" />

            <div className="w-full max-w-md">
                <div className="mb-6">
                    <Link 
                        href="/login" 
                        className="inline-flex items-center gap-2 text-slate-500 hover:text-indigo-600 transition-colors font-medium text-sm group"
                    >
                        <ArrowLeft className="h-4 w-4 group-hover:-translate-x-1 transition-transform" />
                        Retour à la connexion
                    </Link>
                </div>

                <div className="text-center mb-8">
                    <h1 className="text-3xl font-black bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 mb-2">
                        Réinitialisation
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400">
                        Choisissez votre nouveau mot de passe
                    </p>
                </div>

                <GlassCard className="p-8 backdrop-blur-xl border-white/20 dark:border-white/10 shadow-2xl">
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
                                    className="w-full pl-12 pr-12 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-medium placeholder:text-slate-400"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-semibold ml-1 text-slate-700 dark:text-slate-300">Nouveau mot de passe</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                                <input
                                    name="password"
                                    type={showPassword ? "text" : "password"}
                                    required
                                    placeholder="••••••••"
                                    className="w-full pl-12 pr-12 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-medium placeholder:text-slate-400"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                                >
                                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                                </button>
                            </div>
                        </div>

                        {state?.error && (
                            <div className="p-3 text-red-500 text-xs font-semibold text-center bg-red-500/10 rounded-lg border border-red-500/20">
                                {state.error}
                            </div>
                        )}

                        {state?.success && (
                            <div className="p-3 text-emerald-500 text-xs font-semibold text-center bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                                {state.message}. Redirection...
                            </div>
                        )}

                        {!state?.success && <SubmitButton />}
                    </form>
                </GlassCard>
            </div>
        </div>
    );
}
