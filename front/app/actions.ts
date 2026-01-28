"use server";

import { redirect } from "next/navigation";
import { cookies } from "next/headers";

const API_URL = process.env.API_URL || "http://127.0.0.1:8000";

const ERROR_MESSAGES: Record<string, string> = {
    "RULE_MAX_AMOUNT": "Montant supérieur à la limite autorisée (300 PYC).",
    "RULE_INSUFFICIENT_FUNDS": "Solde insuffisant.",
    "RULE_ACCOUNT_LOCKED": "Compte ou portefeuille bloqué. Contactez le support.",
    "RULE_SELF_TRANSFER": "Virement vers soi-même interdit.",
    "RULE_INVALID_AMOUNT": "Montant invalide.",
    "RULE_COUNTRY_BLOCKED": "Destination (pays) non autorisée.",
    "RULE_DESTINATION_LOCKED": "Le portefeuille du destinataire est bloqué.",
    "RULE_AMOUNT_ANOMALY": "Montant inhabituel détecté.",
    "RULE_FREQ_SPIKE": "Trop de transactions récentes. Veuillez patienter.",
    "RULE_NEW_ACCOUNT_ACTIVITY": "Activité suspecte pour un nouveau compte.",
    "RULE_NEW_BENEFICIARY": "Premier virement trop élevé vers ce bénéficiaire.",
    "RULE_GEO_ANOMALY": "Localisation inhabituelle détectée.",
    "RULE_ODD_HOUR": "Transaction à horaire inhabituel bloquée.",
    "RULE_HIGH_RISK_PROFILE": "Refusé : Profil à risque.",
    "RULE_RECIDIVISM": "Refusé suite à de multiples tentatives échouées.",
    "ML_ENGINE_UNAVAILABLE": "Vérification de sécurité indisponible. Réessayez plus tard."
};

export async function createTransferAction(prevState: any, formData: FormData) {
    // ... code truncated for clarity, re-implementing start ...
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
        return { success: false, message: "Erreur de connexion au portefeuille." };
    }

    if (!sourceWalletId) {
        return { success: false, message: "Aucun portefeuille trouvé." };
    }

    const recipient = formData.get("recipient") as string;
    const amountStr = formData.get("amount") as string;
    const amount = parseFloat(amountStr.replace(',', '.'));

    if (isNaN(amount) || amount <= 0) {
        return { success: false, message: "Montant invalide." };
    }

    // 2. Prepare Transaction Payload
    const payload = {
        amount: amount,
        currency: "PYC",
        source_wallet_id: sourceWalletId,
        transaction_type: "TRANSFER",
        direction: "OUTGOING",
        initiator_user_id: userId,
        description: `Virement à ${recipient}`,
        recipient_email: recipient,
        city: "Paris",
        country: "FR"
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
            const errData = await res.json().catch(() => ({ detail: "Erreur inconnue" }));
            return { success: false, message: errData.detail || "Échec de la transaction." };
        }

        const data = await res.json();

        // Check ML Decision
        if (data.decision === "BLOCK" || data.decision === "REJECTED") {
            const rawReasons = data.reasons || [];
            const primaryReason = rawReasons.length > 0 ? rawReasons[0] : "UNKNOWN";

            // Map to Friendly Message or fallback to raw reason
            const friendlyMessage = ERROR_MESSAGES[primaryReason] || `Sécurité : ${primaryReason}`;

            return {
                success: false,
                message: friendlyMessage
            };
        }

        // Success - fallback to redirect below
    } catch (err) {
        console.error("Transaction Exception:", err);
        return { success: false, message: "Erreur réseau. Réessayez." };
    }

    // 4. Redirect to Activity Feed
    redirect("/activity");
}
