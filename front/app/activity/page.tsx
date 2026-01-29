import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { ActivityList } from "@/components/activity/activity-list";
import { Transaction, TransactionStatus } from "@/types/transaction";

const API_URL = process.env.API_URL || "https://sentinelle-api-backend-ntqku76mya-ew.a.run.app";

async function getTransactions(): Promise<Transaction[]> {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token");

    if (!token) return [];

    try {
        const res = await fetch(`${API_URL}/transactions?limit=100`, {
            headers: {
                "Authorization": `Bearer ${token.value}`,
                "Content-Type": "application/json"
            },
            cache: "no-store",
        });

        if (!res.ok) {
            console.error("Failed to fetch transactions:", res.status);
            return [];
        }

        const data = await res.json();

        return data.map((t: any) => ({
            id: t.transaction_id,
            amount: t.amount,
            recipient: t.recipient_name || t.recipient_email || "Inconnu",
            status: t.status as TransactionStatus,
            date: t.created_at,
            direction: t.direction,
            sourceCountry: t.source_country,           // Directement depuis le backend
            destinationCountry: t.destination_country, // Directement depuis le backend
            comment: t.comment,                        // Commentaire depuis le backend
            recipientIban: t.recipient_iban            // IBAN si disponible
        }));

    } catch (error) {
        console.error("Network error fetching transactions:", error);
        return [];
    }
}

export default async function ActivityPage() {
    const transactions = await getTransactions();

    return (
        <div className="space-y-6 max-w-2xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link href="/" className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                    <ArrowLeft className="h-6 w-6" />
                </Link>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold">Historique</h1>
                    <p className="text-sm text-muted-foreground">Vos dernières transactions</p>
                </div>
            </div>

            <ActivityList initialTransactions={transactions} />
        </div>
    );
}
