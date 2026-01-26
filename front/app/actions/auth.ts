"use server";

import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { z } from "zod";

const API_URL = process.env.API_URL || "http://127.0.0.1:8000";

const RegisterSchema = z.object({
    full_name: z.string().min(2),
    email: z.string().email(),
    password: z.string().min(6),
});

const LoginSchema = z.object({
    email: z.string().email(),
    password: z.string().min(1),
});

export async function registerAction(prevState: any, formData: FormData) {
    const data = {
        full_name: formData.get("name"),
        email: formData.get("email"),
        password: formData.get("password"),
    };

    const validated = RegisterSchema.safeParse(data);
    if (!validated.success) {
        return { error: "Données invalides" };
    }

    try {
        const res = await fetch(`${API_URL}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(validated.data),
        });

        if (!res.ok) {
            const errorData = await res.json();
            return { error: errorData.detail || "Erreur lors de l'inscription" };
        }

        const { access_token } = await res.json();
        const cookieStore = await cookies();
        cookieStore.set("auth-token", access_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production", // Consider removing this if local http testing fails
            maxAge: 60 * 60 * 24, // 1 day
            path: "/",
        });
    } catch (err) {
        console.error("Register Error:", err);
        return { error: "Erreur de connexion au serveur" };
    }

    redirect("/");
}

export async function loginAction(prevState: any, formData: FormData) {
    const data = {
        email: formData.get("email"),
        password: formData.get("password"),
    };

    const validated = LoginSchema.safeParse(data);
    if (!validated.success) {
        return { error: "Email ou mot de passe invalide" };
    }

    try {
        const res = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(validated.data),
        });

        if (!res.ok) {
            return { error: "Identifiants incorrects" };
        }

        const { access_token } = await res.json();
        const cookieStore = await cookies();
        cookieStore.set("auth-token", access_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production", // Consider removing this if local http testing fails
            maxAge: 60 * 60 * 24, // 1 day
            path: "/",
        });
    } catch (err) {
        console.error("Login Error:", err);
        return { error: "Erreur de connexion au serveur" };
    }

    redirect("/");
}
