"use server";

import { redirect } from "next/navigation";
import { cookies } from "next/headers";

const API_URL = "https://sentinelle-api-backend-ntqku76mya-ew.a.run.app";

export async function createRequestAction(prevState: any, formData: FormData) {
    const amount = formData.get("amount");
    const recipient = formData.get("recipient") as string;
    const comment = formData.get("comment") as string;
    const knownContacts = formData.get("knownContacts") as string;
    const fromUser = formData.get("fromUser") as string;
    const fromUserName = formData.get("fromUserName") as string; // NEW: display name

    if (!amount || Number(amount) <= 0) {
        return { success: false, message: "Montant invalide." };
    }

    if (!recipient) {
        return { success: false, message: "Destinataire invalide." };
    }

    if (knownContacts && !knownContacts.includes(recipient)) {
        return { success: false, message: "Vous ne pouvez demander de l'argent qu'à un compte existant dans vos contacts." };
    }

    const cookieStore = await cookies();
    const requestsCookie = cookieStore.get("mock_requests");
    let requests: any[] = [];
    if (requestsCookie) {
        try { requests = JSON.parse(requestsCookie.value); } catch (e) {}
    }

    const newRequest = {
        id: "REQ-" + Math.random().toString(36).substr(2, 9).toUpperCase(),
        to: recipient,
        from: fromUser,
        from_name: fromUserName || fromUser, // Save display name
        amount: Number(amount),
        comment: comment || "",
        status: "PENDING",
        direction: "SENT",
        date: new Date().toISOString()
    };

    requests.unshift(newRequest);
    cookieStore.set("mock_requests", JSON.stringify(requests), { path: "/" });

    await new Promise(resolve => setTimeout(resolve, 800));
    redirect("/");
}

export async function actionRespondRequest(id: string, action: 'ACCEPT' | 'DECLINE') {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token");
    const requestsCookie = cookieStore.get("mock_requests");

    let requests: any[] = [];
    if (requestsCookie) {
        try { requests = JSON.parse(requestsCookie.value); } catch (e) {}
    }

    // Find the request (including the fake demo one)
    let req = requests.find((r: any) => r.id === id);
    if (!req && id === "fake-req-001") {
        req = {
            id: "fake-req-001",
            to: cookieStore.get("auth-token") ? "current-user" : "demo",
            from: "service@payon.app",
            from_name: "Service PayOn",
            amount: 50.00,
            comment: "Pour le test d'intégration !",
            status: "PENDING",
            direction: "RECEIVED",
            date: new Date().toISOString()
        };
        requests.push(req);
    }

    if (!req) return;

    if (action === 'ACCEPT' && token) {
        // Trigger real transfer via existing API
        try {
            // 1. Get wallet info
            const dashRes = await fetch(`${API_URL}/dashboard/`, {
                headers: { "Authorization": `Bearer ${token.value}` },
                cache: "no-store",
            });
            if (dashRes.ok) {
                const dash = await dashRes.json();
                const sourceWalletId = dash.wallet?.wallet_id;
                const userId = dash.user?.user_id;

                if (sourceWalletId) {
                    // 2. Post transaction to API
                    await fetch(`${API_URL}/transactions`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            amount: req.amount,
                            currency: "PYC",
                            source_wallet_id: sourceWalletId,
                            transaction_type: "TRANSFER",
                            direction: "OUTGOING",
                            initiator_user_id: userId,
                            description: req.comment || `Suite à demande de ${req.from_name || req.from}`,
                            recipient_email: req.from, // Pay back to the requester
                            city: "Paris",
                            country: "FR",
                            comment: `Paiement suite à demande : ${req.comment || ''}`
                        }),
                    });
                }
            }
        } catch (e) {
            // Silent fail – still mark as accepted in mock
            console.error("Transfer on accept failed:", e);
        }
    }

    // Update mock cookie status
    const idx = requests.findIndex((r: any) => r.id === id);
    if (idx !== -1) {
        requests[idx].status = action === 'ACCEPT' ? 'ACCEPTED' : 'DECLINED';
    }
    cookieStore.set("mock_requests", JSON.stringify(requests), { path: "/" });
}
