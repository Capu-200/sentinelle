"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    Home,
    Send,
    List,
    Settings,
    CreditCard,
    LogOut,
    PieChart
} from "lucide-react";

export const Sidebar = () => {
    const pathname = usePathname();

    const links = [
        { href: "/", label: "Tableau de bord", icon: Home },
        { href: "/transfer", label: "Virements", icon: Send },
        { href: "/activity", label: "Transactions", icon: List },
    ];

    return (
        <aside className="hidden lg:flex fixed left-0 top-0 bottom-0 w-64 flex-col border-r border-slate-200 dark:border-slate-800 bg-background/50 backdrop-blur-xl z-50">
            {/* Logo */}
            <div className="flex h-20 items-center px-8">
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold">
                        P
                    </div>
                    <span className="text-xl font-bold tracking-tight">PAYONE</span>
                </div>
            </div>

            {/* Nav Links */}
            <nav className="flex-1 px-4 py-8 space-y-2">
                {links.map(({ href, label, icon: Icon }) => {
                    const isActive = pathname === href;
                    return (
                        <Link
                            key={href}
                            href={href}
                            className={cn(
                                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium text-sm group relative overflow-hidden",
                                isActive
                                    ? "text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20"
                                    : "text-muted-foreground hover:text-foreground hover:bg-slate-100 dark:hover:bg-white/5"
                            )}
                        >
                            <Icon className={cn("h-5 w-5", isActive && "fill-current")} />
                            <span>{label}</span>
                            {isActive && (
                                <div className="absolute right-0 top-1/2 -translate-y-1/2 h-8 w-1 bg-indigo-600 rounded-l-full" />
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* User Footer */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800">
                <Link
                    href="/profile"
                    className="flex items-center gap-3 w-full px-4 py-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-muted-foreground hover:text-foreground transition-colors group"
                >
                    <Settings className="h-5 w-5" />
                    <span className="text-sm font-medium">Mon Profil</span>
                </Link>
            </div>
        </aside>
    );
};
