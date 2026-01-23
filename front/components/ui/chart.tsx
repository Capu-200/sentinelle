"use client";

import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/utils";

export const AnalyticsChart = () => {
    // Simulated data points
    const points = [20, 45, 28, 80, 50, 90, 30, 60, 40, 75, 55, 95];
    const max = 100;

    return (
        <GlassCard className="h-full p-6 flex flex-col justify-between overflow-hidden">
            <div className="flex items-center justify-between mb-4 z-10 relative">
                <div>
                    <p className="text-sm text-muted-foreground font-medium">Dépenses (7j)</p>
                    <p className="text-2xl font-bold mt-1">1 240,50 €</p>
                </div>
                <div className="px-2 py-1 rounded bg-green-50 text-green-700 text-xs font-bold dark:bg-green-900/30 dark:text-green-400">
                    +12.5%
                </div>
            </div>

            {/* CSS-only Chart */}
            <div className="relative h-32 w-full mt-auto flex items-end justify-between gap-1">
                {points.map((p, i) => (
                    <div
                        key={i}
                        className="w-full bg-indigo-500/20 dark:bg-indigo-400/20 rounded-t-sm relative group"
                        style={{ height: `${p}%` }}
                    >
                        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-indigo-500 to-purple-500 opacity-80 h-full rounded-t-sm transition-all group-hover:opacity-100" />
                    </div>
                ))}
            </div>
        </GlassCard>
    );
};
