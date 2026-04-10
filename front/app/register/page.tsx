'use client';

import { useActionState, useState, useEffect } from 'react';
import { useFormStatus } from 'react-dom';
import { useRouter } from 'next/navigation';
import { GlassCard } from '@/components/ui/glass-card';
import { Eye, EyeOff, Lock, Mail, ArrowRight, Loader2, User, Globe } from 'lucide-react';
import Link from 'next/link';
import { registerAction, AuthActionState } from '../actions/auth';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

const initialState: AuthActionState = {
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
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold shadow-lg shadow-indigo-500/25 active:scale-[0.98] transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 group mt-4"
        >
            {pending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
                <>
                    Créer mon compte
                    <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </>
            )}
        </button>
    );
}

export default function RegisterPage() {
    const router = useRouter();
    const [state, dispatch] = useActionState(registerAction, initialState);
    const [showPassword, setShowPassword] = useState(false);

    // Validation locale simple pour le confirm password
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    useEffect(() => {
        if (state?.error) {
            toast.error(state.error);
        }
        if (state?.success) {
            toast.success('Compte créé avec succès !');
            // Redirection côté client pour garantir que le cookie est bien envoyé
            setTimeout(() => router.push('/'), 100);
        }
    }, [state, router]);

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
                    <h1 className="text-4xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400">
                        Créer un compte
                    </h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-2 font-medium">Rejoignez PayOn dès aujourd&apos;hui</p>
                </div>

                <GlassCard className="p-8 backdrop-blur-xl border-white/20 dark:border-white/10 shadow-2xl">
                    <form
                        action={(formData) => {
                            if (password !== confirmPassword) {
                                toast.error("Les mots de passe ne correspondent pas");
                                return;
                            }
                            dispatch(formData);
                        }}
                        className="space-y-5"
                    >

                        <div className="space-y-2">
                            <label className="text-sm font-semibold ml-1 text-slate-700 dark:text-slate-300">Nom complet</label>
                            <div className="relative group">
                                <User className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                                <input
                                    name="name"
                                    type="text"
                                    required
                                    placeholder="Jacques Dupont"
                                    className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-medium placeholder:text-slate-400"
                                />
                            </div>
                        </div>

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
                            <label className="text-sm font-semibold ml-1 text-slate-700 dark:text-slate-300">Pays de résidence</label>
                            <div className="relative group">
                                <Globe className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                                <select
                                    name="country_home"
                                    required
                                    className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-medium appearance-none text-slate-900 dark:text-slate-200"
                                >
                                    <option value="FR">France</option>
                                    <option value="BE">Belgique</option>
                                    <option value="CH">Suisse</option>
                                    <option value="CA">Canada</option>
                                    <option value="OTHER">Autre</option>
                                </select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 ml-1">Mot de passe</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                                <input
                                    name="password"
                                    type={showPassword ? "text" : "password"}
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
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

                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-slate-700 dark:text-slate-300 ml-1">Confirmer</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                                <input
                                    type={showPassword ? "text" : "password"}
                                    required
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    placeholder="••••••••"
                                    className={cn(
                                        "w-full pl-12 pr-12 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-medium placeholder:text-slate-400",
                                        confirmPassword && password !== confirmPassword && "border-red-500 focus:border-red-500 focus:ring-red-500/50"
                                    )}
                                />
                            </div>
                        </div>

                        {state?.error && (
                            <div className="text-red-500 text-sm font-medium text-center bg-red-500/10 p-2 rounded-lg border border-red-500/20">
                                {state.error}
                            </div>
                        )}

                        <div className="flex items-start gap-3 mt-2">
                            <input 
                                type="checkbox" 
                                required 
                                id="cgu_ia" 
                                name="cgu_ia"
                                className="mt-1 h-4 w-4 shrink-0 rounded border-slate-300 text-indigo-600 focus:ring-indigo-600"
                            />
                            <label htmlFor="cgu_ia" className="text-[11px] leading-relaxed text-slate-500 dark:text-slate-400">
                                J'accepte les CGU et consens explicitement à ce que mes transactions et mon comportement soient analysés par l'<strong>Intelligence Artificielle de PayOn</strong> afin de prévenir la fraude et calculer mon <em>Score de Confiance</em> en temps réel.
                            </label>
                        </div>

                        <SubmitButton />
                    </form>

                    <div className="mt-6 pt-6 border-t border-slate-100 dark:border-white/5 text-center">
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                            Déjà un compte ?{' '}
                            <Link href="/login" className="font-bold text-indigo-600 hover:text-indigo-500 hover:underline">
                                Se connecter
                            </Link>
                        </p>
                    </div>
                </GlassCard>
            </div>
        </div>
    );
}
