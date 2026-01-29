/**
 * 🧪 Exemples de Données de Test
 * 
 * Ce fichier contient des données mockées pour tester l'affichage enrichi des transactions
 */

import { Transaction, TransactionStatus } from "@/types/transaction";

export const mockTransactions: Transaction[] = [
    {
        id: "tx_001",
        amount: 150,
        recipient: "Marie Dubois",
        status: TransactionStatus.VALIDATED,
        date: "2026-01-28T14:30:00Z",
        direction: "INCOMING",
        sourceCountry: "FR",
        destinationCountry: "ES",
        comment: "Remboursement restaurant Madrid",
        recipientIban: "ES9121000418450200051332"
    },
    {
        id: "tx_002",
        amount: 75,
        recipient: "Thomas Martin",
        status: TransactionStatus.PENDING,
        date: "2026-01-28T10:15:00Z",
        direction: "OUTGOING",
        sourceCountry: "FR",
        destinationCountry: "ES",
        comment: "Cadeau d'anniversaire",
    },
    {
        id: "tx_003",
        amount: 250,
        recipient: "Sophie Bernard",
        status: TransactionStatus.ANALYZING,
        date: "2026-01-27T16:45:00Z",
        direction: "OUTGOING",
        sourceCountry: "FR",
        destinationCountry: "DE",
        comment: "Paiement loyer Berlin - Janvier 2026",
    },
    {
        id: "tx_004",
        amount: 50,
        recipient: "Lucas Petit",
        status: TransactionStatus.VALIDATED,
        date: "2026-01-27T09:20:00Z",
        direction: "INCOMING",
        sourceCountry: "BE",
        destinationCountry: "FR",
        // Pas de commentaire sur cette transaction
    },
    {
        id: "tx_005",
        amount: 300,
        recipient: "Emma Rousseau",
        status: TransactionStatus.REJECTED,
        date: "2026-01-26T18:00:00Z",
        direction: "OUTGOING",
        sourceCountry: "FR",
        destinationCountry: "IT",
        comment: "Transaction refusée - montant trop élevé",
    },
    {
        id: "tx_006",
        amount: 120,
        recipient: "Alexandre Moreau",
        status: TransactionStatus.SUSPECT,
        date: "2026-01-26T12:30:00Z",
        direction: "OUTGOING",
        sourceCountry: "FR",
        destinationCountry: "PT",
        comment: "Achat matériel informatique Lisbonne",
    },
    {
        id: "tx_007",
        amount: 85,
        recipient: "Chloé Laurent",
        status: TransactionStatus.VALIDATED,
        date: "2026-01-25T15:10:00Z",
        direction: "INCOMING",
        sourceCountry: "CH",
        destinationCountry: "FR",
        comment: "Remboursement frais déplacement Genève",
        recipientIban: "CH9300762011623852957"
    },
    {
        id: "tx_008",
        amount: 200,
        recipient: "Hugo Girard",
        status: TransactionStatus.VALIDATED,
        date: "2026-01-25T08:45:00Z",
        direction: "OUTGOING",
        sourceCountry: "FR",
        destinationCountry: "NL",
        // Transaction sans commentaire
    }
];

/**
 * 🌍 Codes Pays Supportés
 * 
 * Liste des codes ISO 3166-1 alpha-2 couramment utilisés
 */
export const supportedCountries = {
    FR: "France",
    ES: "Espagne",
    DE: "Allemagne",
    IT: "Italie",
    BE: "Belgique",
    NL: "Pays-Bas",
    PT: "Portugal",
    CH: "Suisse",
    GB: "Royaume-Uni",
    LU: "Luxembourg",
    AT: "Autriche",
    IE: "Irlande",
    GR: "Grèce",
    PL: "Pologne",
    SE: "Suède",
    DK: "Danemark",
    NO: "Norvège",
    FI: "Finlande"
};

/**
 * 📊 Statistiques de Test
 */
export const mockStats = {
    totalTransactions: mockTransactions.length,
    byStatus: {
        validated: mockTransactions.filter(t => t.status === TransactionStatus.VALIDATED).length,
        pending: mockTransactions.filter(t => t.status === TransactionStatus.PENDING).length,
        analyzing: mockTransactions.filter(t => t.status === TransactionStatus.ANALYZING).length,
        rejected: mockTransactions.filter(t => t.status === TransactionStatus.REJECTED).length,
        suspect: mockTransactions.filter(t => t.status === TransactionStatus.SUSPECT).length,
    },
    byDirection: {
        incoming: mockTransactions.filter(t => t.direction === "INCOMING").length,
        outgoing: mockTransactions.filter(t => t.direction === "OUTGOING").length,
    },
    withComments: mockTransactions.filter(t => t.comment && t.comment.trim().length > 0).length,
    withCountryInfo: mockTransactions.filter(t => t.sourceCountry && t.destinationCountry).length,
    corridors: Array.from(new Set(
        mockTransactions
            .filter(t => t.sourceCountry && t.destinationCountry)
            .map(t => `${t.sourceCountry} → ${t.destinationCountry}`)
    ))
};

/**
 * 💬 Exemples de Commentaires
 * 
 * Suggestions pour les utilisateurs
 */
export const commentSuggestions = [
    "Remboursement dîner",
    "Cadeau d'anniversaire",
    "Loyer mensuel",
    "Achat matériel",
    "Frais de déplacement",
    "Paiement facture",
    "Prêt personnel",
    "Partage de frais",
    "Achat en ligne",
    "Services professionnels"
];

/**
 * 🧪 Fonction Helper pour Tester
 */
export const getTransactionById = (id: string): Transaction | undefined => {
    return mockTransactions.find(t => t.id === id);
};

export const getTransactionsByCountryCorridor = (from: string, to: string): Transaction[] => {
    return mockTransactions.filter(
        t => t.sourceCountry === from && t.destinationCountry === to
    );
};

export const getTransactionsWithComments = (): Transaction[] => {
    return mockTransactions.filter(t => t.comment && t.comment.trim().length > 0);
};

export const getTransactionsWithoutComments = (): Transaction[] => {
    return mockTransactions.filter(t => !t.comment || t.comment.trim().length === 0);
};
