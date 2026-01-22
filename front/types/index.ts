export type TransactionStatus = 'validated' | 'pending' | 'blocked' | 'verifying';

export type TransactionType = 'sent' | 'received';

export interface Transaction {
  id: string;
  type: TransactionType;
  amount: number;
  recipient?: string;
  sender?: string;
  date: Date;
  status: TransactionStatus;
  reason?: string;
}

export interface Contact {
  id: string;
  name: string;
  avatar?: string;
  isFavorite: boolean;
}

export interface Wallet {
  balance: number;
  currency: string;
}

export interface UserProfile {
  name: string;
  email: string;
  kycStatus: 'verified' | 'pending' | 'unverified';
  paymentMethods: PaymentMethod[];
}

export interface PaymentMethod {
  id: string;
  type: 'iban' | 'card';
  label: string;
  last4?: string;
}

