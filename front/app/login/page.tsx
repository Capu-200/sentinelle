'use client';

import { useActionState, useState, useEffect } from 'react';
import { useFormStatus } from 'react-dom';
import { GlassCard } from '@/components/ui/glass-card';
import { Eye, EyeOff, Lock, Mail, ArrowRight, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { loginAction } from '../actions/auth';
import toast from 'react-hot-toast';

const initialState = {
    error: '',
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
                    Se connecter
                    <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </>
            )}
        </button>
    );
}

export default function LoginPage() {
    const [state, dispatch] = useActionState(loginAction, initialState);
    const [showPassword, setShowPassword] = useState(false);

    useEffect(() => {
        if (state?.error) {
            toast.error(state.error);
        }
    }, [state]);

    return (
        <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
            {/* Animated Background */}
            <div className="absolute inset-0 bg-slate-50 dark:bg-[#050505] z-0" />

            {/* Ambient Orbs */}
            <div className="absolute top-[-10%] left-[-10%] h-[500px] w-[500px] rounded-full bg-indigo-600/30 blur-[120px] mix-blend-screen animate-pulse z-0" />
            <div className="absolute bottom-[-10%] right-[-10%] h-[500px] w-[500px] rounded-full bg-purple-600/20 blur-[120px] mix-blend-screen animate-pulse z-0 duration-700" />

            <div className="w-full max-w-md z-10 relative">
                {/* Logo Section */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center p-3 bg-white/10 backdrop-blur-md rounded-2xl mb-4 shadow-lg border border-white/20">
                        <div className="h-8 w-8 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-lg flex items-center justify-center shadow-inner">
                            <Lock className="text-white h-4 w-4" />
                        </div>
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400">
                        PayOn
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-2 font-medium">Des virements sécurisés</p>
                </div>

                <GlassCard className="p-8 backdrop-blur-xl border-white/20 dark:border-white/10 shadow-2xl">
                    <form action={dispatch} className="space-y-5">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold ml-1 text-slate-700 dark:text-slate-300">Email</label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                                <input
                                    name="email"
                                    type="email"
                                    required
                                    placeholder="jacques@payon.app"
                                    className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-medium placeholder:text-slate-400"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between items-center ml-1">
                                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Mot de passe</label>
                                <Link href="#" className="text-xs font-semibold text-indigo-600 hover:text-indigo-500 hover:underline">Oublié ?</Link>
                            </div>
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
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 focus:outline-none"
                                >
                                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                                </button>
                            </div>
                        </div>

                        {state?.error && (
                            <div className="text-red-500 text-sm font-medium text-center bg-red-500/10 p-2 rounded-lg border border-red-500/20">
                                {state.error}
                            </div>
                        )}

                        <SubmitButton />
                    </form>

                    <div className="mt-6 pt-6 border-t border-slate-100 dark:border-white/5 text-center">
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                            Pas encore de compte ?{' '}
                            <Link href="/register" className="font-bold text-indigo-600 hover:text-indigo-500 hover:underline">
                                Créer un compte
                            </Link>
                        </p>
                    </div>
                </GlassCard>

                {/* Secure Badge */}
                <div className="mt-8 flex justify-center items-center gap-2 text-xs text-slate-400 font-medium opacity-60">
                    <Lock className="h-3 w-3" />
                    <span>Connexion sécurisée SSL 256-bit</span>
                </div>
            </div>
        </div>
    );
}
