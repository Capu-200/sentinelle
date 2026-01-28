'use server';

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";

const API_URL = process.env.API_URL || "https://sentinelle-api-backend-8773685706613.europe-west1.run.app";

export async function addContactAction(formData: FormData) {
    const name = formData.get("name") as string;
    const email = formData.get("email") as string;
    const iban = formData.get("iban") as string;

    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token");

    if (!token) {
        return { success: false, error: "Unauthorized" };
    }

    try {
        const payload: any = { name };
        if (email) payload.email = email;
        if (iban) payload.iban = iban;

        const res = await fetch(`${API_URL}/contacts/`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token.value}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const error = await res.json();
            return { success: false, error: error.detail || "Failed to add contact" };
        }

        revalidatePath("/contacts");
        return { success: true };
    } catch (error) {
        return { success: false, error: "Network error" };
    }
}

export async function deleteContactAction(contactId: string) {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token");

    if (!token) return { success: false, error: "Unauthorized" };

    try {
        const res = await fetch(`${API_URL}/contacts/${contactId}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token.value}`
            }
        });

        if (!res.ok) {
            const txt = await res.text();
            console.error(`Delete failed: ${res.status} - ${txt}`);
            return { success: false, error: "Failed to delete" };
        }


        revalidatePath("/contacts");
        return { success: true };
    } catch (error) {
        return { success: false, error: "Network error" };
    }
}

export async function getContactsAction() {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token");
    if (!token) return [];

    try {
        const res = await fetch(`${API_URL}/contacts/`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token.value}`,
                "Content-Type": "application/json"
            },
            cache: "no-store"
        });

        if (!res.ok) {
            return [];
        }

        return await res.json();
    } catch (error) {
        return [];
    }
}