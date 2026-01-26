"use server";

import { redirect } from "next/navigation";
import { cookies } from "next/headers";

const API_URL = process.env.API_URL || "http://127.0.0.1:8000";

export async function createTransferAction(formData: FormData) {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token");

    if (!token) {
        redirect("/login");
    }

    // 1. Fetch User's Wallet ID (Source)
    let sourceWalletId = "";
    let userId = "";

    try {
        const dashboardRes = await fetch(`${API_URL}/dashboard/`, {
            headers: {
                "Authorization": `Bearer ${token.value}`,
            },
            cache: "no-store",
        });

        if (dashboardRes.ok) {
            const data = await dashboardRes.json();
            if (data.wallet) {
                sourceWalletId = data.wallet.wallet_id;
                userId = data.user.user_id;
            }
        }
    } catch (e) {
        console.error("Failed to fetch wallet info", e);
        // We could return an error state here if we had a way to display it on the form without useFormState (simple action)
        // For now, let's proceed and fail at the next step if ID is missing.
    }

    if (!sourceWalletId) {
        console.error("No source wallet found for user");
        // In a real app, return { error: "..." } and handle in component
        redirect("/?error=no_wallet");
    }

    const recipient = formData.get("recipient") as string;
    const amountStr = formData.get("amount") as string;
    const amount = parseFloat(amountStr.replace(',', '.')); // Handle potential comma

    if (isNaN(amount) || amount <= 0) {
        // Invalid amount
        return;
    }

    // 2. Prepare Transaction Payload
    // Backend expects: TransactionRequest
    const payload = {
        amount: amount,
        currency: "EUR",
        source_wallet_id: sourceWalletId,
        transaction_type: "TRANSFER",
        direction: "OUTGOING",
        initiator_user_id: userId,
        description: `Virement vers ${recipient}`, // Store recipient name here for now
        // destination_wallet_id: null, // Left empty for external/unresolved
        city: "Paris", // Default for MVP
        country: "FR"  // Default for MVP
    };

    // 3. Send to Backend
    try {
        const res = await fetch(`${API_URL}/transactions`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const err = await res.text();
            console.error("Transaction failed:", err);
            // Handle error (redirect to error page or ?error=...)
            redirect("/transfer?error=failed");
        }

        // Success
        await res.json(); // Consume body

    } catch (err) {
        console.error("Transaction Exception:", err);
        // Check if it's a redirect error (NEXT_REDIRECT)
        if ((err as any).message === "NEXT_REDIRECT") throw err;
        redirect("/transfer?error=network");
    }

    // 4. Redirect to Activity Feed
    redirect("/activity");
}
