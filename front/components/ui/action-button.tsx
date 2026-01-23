import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";
import Link from "next/link";

interface ActionButtonProps {
    icon: LucideIcon;
    label: string;
    href?: string;
    onClick?: () => void;
    variant?: "primary" | "secondary" | "accent";
}

export const ActionButton = ({ icon: Icon, label, href, onClick, variant = "secondary" }: ActionButtonProps) => {
    const baseStyles = cn(
        "flex items-center justify-center gap-3 w-full p-4 rounded-xl shadow-sm transition-all active:scale-95 group border cursor-pointer select-none",
        variant === "primary" && "bg-primary text-primary-foreground border-primary hover:shadow-md",
        variant === "secondary" && "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700 hover:border-indigo-500 dark:hover:border-indigo-500 hover:shadow-md",
        variant === "accent" && "bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700 hover:shadow-indigo-500/25 shadow-indigo-500/20"
    );

    const content = (
        <>
            <Icon className={cn("h-5 w-5", variant === "accent" ? "text-white" : "text-indigo-600 dark:text-indigo-400")} />
            <span className="font-semibold text-sm">{label}</span>
        </>
    );

    if (href) {
        return (
            <Link href={href} className={baseStyles}>
                {content}
            </Link>
        );
    }

    // Interactive button
    return (
        <button onClick={onClick} className={baseStyles} type="button">
            {content}
        </button>
    );
};
