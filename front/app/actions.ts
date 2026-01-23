"use server";

import { redirect } from "next/navigation";

export async function createTransferAction(formData: FormData) {
    const recipient = formData.get("recipient") as string;
    const amount = formData.get("amount") as string;

    // Mock processing delay to simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // In a real app, this would call your NestJS/FastAPI backend
    // For now, we generate a fake ID and simulate a "PENDING" state creation
    const transactionId = Math.random().toString(36).substring(7);

    console.log(`[Server Action] Created transaction ${transactionId} for ${amount}€ to ${recipient}`);

    // Redirect to the tracking page
    redirect(`/activity/${transactionId}?amount=${amount}`);
}
