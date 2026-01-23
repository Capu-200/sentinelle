"use client";

import { useEffect, useState } from 'react';
import { TransactionStatus } from '@/types/transaction';

export const useTransactionSocket = (transactionId: string) => {
    const [status, setStatus] = useState<TransactionStatus>(TransactionStatus.PENDING);

    useEffect(() => {
        if (!transactionId) return;

        // Mock socket connection and events
        console.log(`[Socket] Connecting to channel transaction:${transactionId}`);

        const timers: NodeJS.Timeout[] = [];

        // Simulate event: ANALYZING after 1.5s
        timers.push(setTimeout(() => {
            console.log(`[Socket] Event received: STATUS_UPDATE -> ANALYZING`);
            setStatus(TransactionStatus.ANALYZING);
        }, 1500));

        // Simulate event: SUSPECT Logic (Mocking Persona Pierre scenario)
        timers.push(setTimeout(() => {
            // 50% chance of being suspect
            const isSuspect = Math.random() > 0.5;

            if (isSuspect) {
                console.log(`[Socket] Event received: RISK_ALERT -> SUSPECT`);
                setStatus(TransactionStatus.SUSPECT);

                // Simulate Admin Action (Thomas) validating after 5s delay
                timers.push(setTimeout(() => {
                    console.log(`[Socket] Event received: ADMIN_VALIDATION -> VALIDATED`);
                    setStatus(TransactionStatus.VALIDATED);
                }, 5000));

            } else {
                const finalStatus = Math.random() > 0.1 ? TransactionStatus.VALIDATED : TransactionStatus.REJECTED;
                setStatus(finalStatus);
            }
        }, 4000));

        return () => {
            console.log(`[Socket] Disconnecting...`);
            timers.forEach(clearTimeout);
        };
    }, [transactionId]);

    return { status };
};
