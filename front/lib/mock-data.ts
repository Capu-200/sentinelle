import { Transaction, Contact, Wallet, UserProfile } from '@/types';

export const mockWallet: Wallet = {
  balance: 1250.50,
  currency: 'EUR',
};

export const mockContacts: Contact[] = [
  { id: '1', name: 'Marie Dubois', isFavorite: true },
  { id: '2', name: 'Jean Martin', isFavorite: true },
  { id: '3', name: 'Sophie Bernard', isFavorite: false },
  { id: '4', name: 'Pierre Durand', isFavorite: false },
  { id: '5', name: 'Emma Leroy', isFavorite: true },
];

export const mockTransactions: Transaction[] = [
  {
    id: '1',
    type: 'received',
    amount: 50.00,
    sender: 'Marie Dubois',
    date: new Date(Date.now() - 1000 * 60 * 30), // 30 min ago
    status: 'validated',
  },
  {
    id: '2',
    type: 'sent',
    amount: 25.50,
    recipient: 'Jean Martin',
    date: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2h ago
    status: 'validated',
  },
  {
    id: '3',
    type: 'sent',
    amount: 100.00,
    recipient: 'Sophie Bernard',
    date: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
    status: 'validated',
  },
  {
    id: '4',
    type: 'sent',
    amount: 200.00,
    recipient: 'Pierre Durand',
    date: new Date(Date.now() - 1000 * 60 * 60 * 48), // 2 days ago
    status: 'blocked',
    reason: 'Transaction bloquée pour votre sécurité',
  },
];

export const mockProfile: UserProfile = {
  name: 'Alexandre Moreau',
  email: 'alexandre.moreau@example.com',
  kycStatus: 'verified',
  paymentMethods: [
    { id: '1', type: 'iban', label: 'IBAN •••• 1234' },
    { id: '2', type: 'card', label: 'Carte •••• 5678', last4: '5678' },
  ],
};

