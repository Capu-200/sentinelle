"use server";

import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { z } from "zod";

const API_URL = process.env.API_URL || "https://sentinelle-api-backend-ntqku76mya-ew.a.run.app";

const RegisterSchema = z.object({
    full_name: z.string().min(2),
    email: z.string().email(),
    password: z.string().min(6),
});

const LoginSchema = z.object({
    email: z.string().email(),
    password: z.string().min(1),
});

export async function registerAction(prevState: AuthActionState, formData: FormData): Promise<AuthActionState> {
    const data = {
        full_name: formData.get("name"),
        email: formData.get("email"),
        password: formData.get("password"),
    };

    const validated = RegisterSchema.safeParse(data);
    if (!validated.success) {
        return { error: "Données invalides", success: false, message: "" };
    }

    try {
        const res = await fetch(`${API_URL}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(validated.data),
        });

        if (!res.ok) {
            const errorData = await res.json();
            if (Array.isArray(errorData.detail)) {
                const messages = errorData.detail.map((err: { loc: (string | number)[]; msg: string }) =>
                    `${err.loc[1] || 'Champ'}: ${err.msg}`
                ).join('. ');
                return { error: messages, success: false, message: "" };
            }
            return { error: errorData.detail || "Erreur lors de l'inscription", success: false, message: "" };
        }

        const { access_token } = await res.json();
        const cookieStore = await cookies();

        const isSecureContext = process.env.VERCEL === '1' || process.env.NODE_ENV === 'production';
        console.log(`[REGISTER] Setting cookie - SecureContext: ${isSecureContext}`);

        cookieStore.set("auth-token", access_token, {
            httpOnly: true,
            secure: isSecureContext,
            sameSite: 'lax',
            maxAge: 60 * 60 * 24 * 7,
            path: "/",
        });
    } catch (err) {
        if ((err as Error).message === "NEXT_REDIRECT") throw err;
        console.error("Register Error:", err);
        return { error: "Erreur de connexion au serveur", success: false, message: "" };
    }

    return { success: true, error: '', message: "Compte créé avec succès" };
}

export async function loginAction(prevState: AuthActionState, formData: FormData): Promise<AuthActionState> {
    const data = {
        email: formData.get("email"),
        password: formData.get("password"),
    };

    const validated = LoginSchema.safeParse(data);
    if (!validated.success) {
        return { error: "Email ou mot de passe invalide", success: false, message: "" };
    }

    try {
        console.log(`[LOGIN] Attempting login for: ${validated.data.email}`);
        console.log(`[LOGIN] API_URL: ${API_URL}`);

        const res = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(validated.data),
        });

        console.log(`[LOGIN] Response status: ${res.status}`);

        if (!res.ok) {
            const errorText = await res.text();
            console.error(`[LOGIN] Error response: ${errorText}`);
            return { error: "Identifiants incorrects", success: false, message: "" };
        }

        const { access_token } = await res.json();
        const cookieStore = await cookies();

        // VERCEL=1 is automatically injected by Vercel — more reliable than NODE_ENV
        const isSecureContext = process.env.VERCEL === '1' || process.env.NODE_ENV === 'production';
        console.log(`[LOGIN] Setting cookie - SecureContext: ${isSecureContext}, VERCEL: ${process.env.VERCEL}`);

        cookieStore.set("auth-token", access_token, {
            httpOnly: true,
            secure: isSecureContext,
            sameSite: 'lax',
            maxAge: 60 * 60 * 24 * 7,
            path: "/",
        });
    } catch (err) {
        if ((err as Error).message === "NEXT_REDIRECT") throw err;
        console.error("Login Error:", err);
        return { error: "Erreur de connexion au serveur", success: false, message: "" };
    }

    return { success: true, error: '', message: "Connexion réussie" };
}

export async function logoutAction() {
    const cookieStore = await cookies();
    cookieStore.delete("auth-token");
    redirect("/login");
}

export async function deleteAccountAction() {
    const cookieStore = await cookies();
    const token = cookieStore.get("auth-token")?.value;
    
    if (token) {
        try {
            // Appeler la nouvelle route backend qui fait current_user.is_active = False
            await fetch(`${API_URL}/auth/archive`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });
        } catch (e) {
            console.error("Erreur gérée silencieusement lors de l'archivage RGPD", e);
        }
    }

    cookieStore.delete("auth-token");
    return { success: true };
}

// Unified state type — required to avoid useActionState overload TS error on Vercel
export type AuthActionState = { error: string; success: boolean; message: string };

export async function forgotPasswordAction(
    prevState: AuthActionState,
    formData: FormData
): Promise<AuthActionState> {
    const email = formData.get("email") as string;

    if (!email || !email.includes("@")) {
        return { error: "Email invalide.", success: false, message: "" };
    }

    try {
        const res = await fetch(`${API_URL}/auth/forgot-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });

        if (!res.ok) {
            return { error: "Erreur lors de l'envoi. Réessayez.", success: false, message: "" };
        }

        const data = await res.json();
        return {
            success: true,
            error: "",
            message: data.reset_link || data.message || "Lien de réinitialisation généré.",
        };
    } catch {
        return { error: "Erreur réseau. Réessayez.", success: false, message: "" };
    }
}

export async function resetPasswordAction(
    prevState: AuthActionState,
    formData: FormData
): Promise<AuthActionState> {
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;
    const confirm = formData.get("confirm") as string;

    if (!password || password.length < 6) {
        return { error: "Le mot de passe doit contenir au moins 6 caractères.", success: false, message: "" };
    }

    if (password !== confirm) {
        return { error: "Les mots de passe ne correspondent pas.", success: false, message: "" };
    }

    try {
        const res = await fetch(`${API_URL}/auth/reset-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, new_password: password }),
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            return { error: errorData.detail || "Erreur lors de la réinitialisation.", success: false, message: "" };
        }

        return { success: true, error: "", message: "Mot de passe mis à jour avec succès !" };
    } catch {
        return { error: "Erreur réseau. Réessayez.", success: false, message: "" };
    }
}