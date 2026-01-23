"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Home, Send, List, ShieldCheck } from "lucide-react";

export const Header = () => {
    return (
        <header className="sticky top-0 z-50 w-full border-b-0 bg-transparent backdrop-blur-sm px-4 py-4 lg:hidden">
            <div className="container flex items-center max-w-md mx-auto md:max-w-2xl">
                <div className="flex items-center gap-2 font-bold text-lg">
                    <ShieldCheck className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                    <span>PayOn</span>
                </div>
                <div className="ml-auto">
                    <div className="h-8 w-8 rounded-full bg-slate-200 dark:bg-slate-800" />
                </div>
            </div>
        </header>
    );
};

export const BottomNav = () => {
    const pathname = usePathname();

    const links = [
        { href: "/", label: "Accueil", icon: Home },
        { href: "/transfer", label: "Envoyer", icon: Send },
        { href: "/activity", label: "Activité", icon: List },
    ];

    return (
        <nav className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/80 backdrop-blur-md px-6 py-2 pb-safe-area-bottom md:hidden border-slate-200 dark:border-slate-800 lg:hidden">
            <div className="flex items-center justify-between max-w-md mx-auto">
                {links.map(({ href, label, icon: Icon }) => {
                    const isActive = pathname === href;
                    return (
                        <Link
                            key={href}
                            href={href}
                            className={cn(
                                "flex flex-col items-center gap-1 p-2 rounded-lg transition-colors",
                                isActive
                                    ? "text-indigo-600 dark:text-indigo-400"
                                    : "text-muted-foreground hover:text-foreground"
                            )}
                        >
                            <Icon className={cn("h-6 w-6 transition-transform active:scale-95", isActive && "fill-current")} />
                            <span className="text-[10px] font-medium">{label}</span>
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
};
