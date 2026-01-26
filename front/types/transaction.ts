export enum TransactionStatus {
    PENDING = 'PENDING',
    ANALYZING = 'ANALYZING',
    SUSPECT = 'SUSPECT',
    VALIDATED = 'VALIDATED',
    REJECTED = 'REJECTED',
}

export interface Transaction {
    id: string;
    amount: number;
    recipient: string;
    status: TransactionStatus;
    date: string; // ISO string
    direction?: 'INCOMING' | 'OUTGOING';
}
