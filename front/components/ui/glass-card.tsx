import { cn } from "@/lib/utils";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    gradient?: boolean;
}

export const GlassCard = ({ children, className, gradient = false, ...props }: GlassCardProps) => {
    return (
        <div
            className={cn(
                "relative overflow-hidden rounded-3xl border border-white/20 shadow-xl backdrop-blur-md",
                gradient
                    ? "bg-gradient-to-br from-indigo-500/90 via-purple-500/90 to-pink-500/90 text-white"
                    : "bg-white/60 dark:bg-slate-900/60",
                className
            )}
            {...props}
        >
            {/* Noise Texture Overlay (Optional for extra texture) */}
            {gradient && (
                <div className="absolute inset-0 z-0 bg-white/5 opacity-50" style={{ backgroundImage: "url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjZmZmIiBmaWxsLW9wYWNpdHk9IjAuMDUiLz4KPC9zdmc+') " }} />
            )}

            <div className="relative z-10">
                {children}
            </div>
        </div>
    );
};
