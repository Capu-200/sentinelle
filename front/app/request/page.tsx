import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { cookies } from "next/headers";
import { RequestForm } from "./request-form";

const API_URL = "https://sentinelle-api-backend-ntqku76mya-ew.a.run.app";

async function getContacts() {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token");
    if (!token) {
        return { contacts: [], user: null };
    }

    try {
        const res = await fetch(`${API_URL}/contacts/`, {
            headers: { "Authorization": `Bearer ${token.value}` },
            cache: "no-store"
        });

        // Use dashboard to get full user info
        const dashRes = await fetch(`${API_URL}/dashboard/`, {
            headers: { "Authorization": `Bearer ${token.value}` },
            cache: "no-store"
        });

        const contacts = res.ok ? await res.json() : [];
        const dashData = dashRes.ok ? await dashRes.json() : null;
        const user = dashData?.user || null;
        
        return { contacts, user };
    } catch (e) {
        return { contacts: [], user: null };
    }
}

export default async function RequestPage() {
    const { contacts, user } = await getContacts();

    return (
        <div className="flex min-h-[80vh] flex-col">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <Link href="/" className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                    <ArrowLeft className="h-6 w-6" />
                </Link>
                <h1 className="text-xl font-bold">Demander de l'argent</h1>
            </div>

            <RequestForm 
                contacts={contacts} 
                currentUserEmail={user?.email} 
                currentUserName={[user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email}
            />
        </div>
    );
}
