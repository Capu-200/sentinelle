'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { mockWallet, mockTransactions, mockContacts } from '@/lib/mock-data';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Skeleton from '@/components/ui/Skeleton';
import TransactionItem from '@/components/TransactionItem';

export default function Home() {
  const [balance, setBalance] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    // Simuler le chargement du solde
    const timer = setTimeout(() => {
      setBalance(mockWallet.balance);
      setIsLoading(false);
    }, 800);
    
    return () => clearTimeout(timer);
  }, []);
  
  const recentTransactions = mockTransactions.slice(0, 3);
  const favoriteContacts = mockContacts.filter(c => c.isFavorite).slice(0, 4);
  
  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-100 px-4 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Sentinelle</h1>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Sécurisé par IA
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="px-4 py-6 space-y-6">
        {/* Balance Card */}
        <Card className="bg-gradient-to-br from-orange-500 via-orange-400 to-blue-500 text-white border-0 shadow-lg animate-fade-in">
          <div className="text-sm opacity-90 mb-2">Solde disponible</div>
          {isLoading ? (
            <Skeleton className="h-12 w-48 bg-white/20" />
          ) : error ? (
            <div className="text-red-200">Erreur de chargement</div>
          ) : (
            <div className="text-4xl font-bold mb-4 animate-slide-up">
              {balance?.toFixed(2)} €
            </div>
          )}
          <div className="text-xs opacity-75">
            Transactions sécurisées par intelligence artificielle
          </div>
        </Card>
        
        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <Link href="/send">
            <Button variant="primary" size="lg" className="w-full">
              Envoyer
            </Button>
          </Link>
          <Link href="/receive">
            <Button variant="secondary" size="lg" className="w-full">
              Recevoir
            </Button>
          </Link>
        </div>
        
        {/* Favorite Contacts */}
        {favoriteContacts.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Contacts favoris</h2>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {favoriteContacts.map((contact) => (
                <Link
                  key={contact.id}
                  href={`/send?contact=${contact.id}`}
                  className="flex flex-col items-center gap-2 min-w-[80px]"
                >
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-400 to-blue-400 flex items-center justify-center text-white text-xl font-semibold shadow-md">
                    {contact.name.charAt(0)}
                  </div>
                  <span className="text-xs text-gray-700 text-center truncate w-full">
                    {contact.name.split(' ')[0]}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}
        
        {/* Recent Transactions */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">Dernières transactions</h2>
            <Link href="/history" className="text-sm text-orange-500 font-medium">
              Voir tout
            </Link>
          </div>
          
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3 p-4 bg-white rounded-xl">
                  <Skeleton className="w-12 h-12 rounded-full" variant="circular" />
                  <div className="flex-1">
                    <Skeleton className="h-4 w-32 mb-2" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                  <Skeleton className="h-6 w-20" />
                </div>
              ))}
            </div>
          ) : recentTransactions.length === 0 ? (
            <Card className="text-center py-8">
              <div className="text-4xl mb-2">💳</div>
              <p className="text-gray-500">Aucune transaction récente</p>
            </Card>
          ) : (
            <div className="space-y-2">
              {recentTransactions.map((transaction) => (
                <Link key={transaction.id} href={`/history/${transaction.id}`}>
                  <TransactionItem transaction={transaction} />
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
