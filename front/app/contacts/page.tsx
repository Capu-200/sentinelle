import { GlassCard } from "@/components/ui/glass-card";
import { ArrowLeft, Plus, Search, User, Trash2, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { cookies } from "next/headers";
import { ContactList } from "./contact-list";

const API_URL = process.env.API_URL || "https://sentinelle-api-backend-8773685706613.europe-west1.run.app";

// Server Component for fetching initial data
async function getContacts() {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token");
    if (!token) return [];

    try {
        const res = await fetch(`${API_URL}/contacts/`, {
            headers: { "Authorization": `Bearer ${token.value}` },
            cache: "no-store"
        });
        if (!res.ok) return [];
        return await res.json();
    } catch (e) {
        return [];
    }
}

export default async function ContactsPage() {
    const contacts = await getContacts();

    return (
        <div className="max-w-2xl mx-auto space-y-6 pb-20 relative">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link href="/" className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                    <ArrowLeft className="h-6 w-6" />
                </Link>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold">Mes Contacts</h1>
                    <p className="text-sm text-muted-foreground">Gérez vos bénéficiaires</p>
                </div>
            </div>

            {/* Client Component handles Search, Modals and Interactions */}
            <ContactList initialContacts={contacts} />
        </div>
    );
}
