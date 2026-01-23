'use client';

import { usePathname } from "next/navigation";
import { BottomNav, Header } from "@/components/layout/navigation";
import { Sidebar } from "@/components/layout/sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const isAuthPage = pathname === "/login" || pathname === "/register";

    if (isAuthPage) {
        return <>{children}</>;
    }

    return (
        <div className="relative flex min-h-full z-10">
            {/* Desktop Sidebar (Fixed) */}
            <Sidebar />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col lg:pl-64 transition-all w-full">

                {/* Mobile Header */}
                <Header />

                {/* Page Content */}
                <main className="flex-1 container max-w-md mx-auto lg:max-w-7xl px-4 py-8 pb-24 md:pb-12 lg:px-8 lg:py-10">
                    {children}
                </main>

                {/* Mobile Bottom Nav */}
                <BottomNav />
            </div>
        </div>
    );
}
