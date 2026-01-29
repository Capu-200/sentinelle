"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";

const API_URL = process.env.API_URL || "https://sentinelle-api-backend-ntqku76mya-ew.a.run.app";

interface UpdateCommentResult {
    success: boolean;
    message: string;
}

/**
 * Server Action pour ajouter/modifier un commentaire sur une transaction existante
 * Cette action ne passe PAS par l'API ML - c'est une simple mise à jour de métadonnées
 */
export async function updateTransactionCommentAction(
    transactionId: string,
    comment: string
): Promise<UpdateCommentResult> {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token");

    if (!token) {
        return { success: false, message: "Non authentifié" };
    }

    // Validation du commentaire
    if (!comment || comment.trim().length === 0) {
        return { success: false, message: "Le commentaire ne peut pas être vide" };
    }

    if (comment.length > 500) {
        return { success: false, message: "Le commentaire est trop long (max 500 caractères)" };
    }

    try {
        const res = await fetch(`${API_URL}/transactions/${transactionId}/comment`, {
            method: "PATCH",
            headers: {
                "Authorization": `Bearer ${token.value}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ comment: comment.trim() }),
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({ detail: "Erreur inconnue" }));
            return { success: false, message: errData.detail || "Échec de la mise à jour" };
        }

        // Revalider les pages qui affichent les transactions
        revalidatePath("/activity");
        revalidatePath("/history");
        revalidatePath("/");

        return { success: true, message: "Commentaire ajouté avec succès" };
    } catch (err) {
        console.error("Update comment exception:", err);
        return { success: false, message: "Erreur réseau. Réessayez." };
    }
}
