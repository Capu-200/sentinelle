import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { cookies } from "next/headers";
import { TransferForm } from "./transfer-form";

async function getContacts() {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token");
    if (!token) {
        console.log("TransferPage: No token found");
        return [];
    }

    try {
        console.log("TransferPage: Fetching contacts...");
        const res = await fetch("http://127.0.0.1:8000/contacts/", {
            headers: { "Authorization": `Bearer ${token.value}` },
            cache: "no-store"
        });

        if (!res.ok) {
            console.error(`TransferPage: Fetch failed with status ${res.status}`);
            return [];
        }
        const data = await res.json();
        console.log(`TransferPage: Fetched ${data.length} contacts`);
        return data;
    } catch (e) {
        console.error("TransferPage: Network error", e);
        return [];
    }
}

export default async function TransferPage() {
    const contacts = await getContacts();

    return (
        <div className="flex min-h-[80vh] flex-col">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <Link href="/" className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                    <ArrowLeft className="h-6 w-6" />
                </Link>
                <h1 className="text-xl font-bold">Effectuer un virement</h1>
            </div>

            <TransferForm contacts={contacts} />
        </div>
    );
}
