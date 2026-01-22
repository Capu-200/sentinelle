'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { mockTransactions } from '@/lib/mock-data';
import TransactionItem from '@/components/TransactionItem';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { ClipboardDocumentListIcon } from '@heroicons/react/24/outline';

type Filter = 'all' | 'sent' | 'received';

export default function HistoryPage() {
  const router = useRouter();
  const [filter, setFilter] = useState<Filter>('all');
  
  const filteredTransactions = mockTransactions.filter((t) => {
    if (filter === 'all') return true;
    return t.type === filter;
  });
  
  const totalSent = mockTransactions
    .filter(t => t.type === 'sent' && t.status === 'validated')
    .reduce((sum, t) => sum + t.amount, 0);
  
  const totalReceived = mockTransactions
    .filter(t => t.type === 'received' && t.status === 'validated')
    .reduce((sum, t) => sum + t.amount, 0);
  
  return (
    <div className="min-h-screen pb-20">
      <main className="px-4 py-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <div className="text-sm text-gray-500 mb-1">Envoyé</div>
            <div className="text-2xl font-bold text-gray-900">{totalSent.toFixed(2)} €</div>
          </Card>
          <Card>
            <div className="text-sm text-gray-500 mb-1">Reçu</div>
            <div className="text-2xl font-bold text-green-600">{totalReceived.toFixed(2)} €</div>
          </Card>
        </div>
        
        {/* Filters */}
        <div className="flex gap-2">
          {(['all', 'sent', 'received'] as Filter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                filter === f
                  ? 'bg-gradient-to-r from-orange-500 to-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {f === 'all' ? 'Tout' : f === 'sent' ? 'Envoyées' : 'Reçues'}
            </button>
          ))}
        </div>
        
        {/* Transactions List */}
        {filteredTransactions.length === 0 ? (
          <Card className="text-center py-12">
            <ClipboardDocumentListIcon className="w-16 h-16 mx-auto mb-2 text-gray-400" />
            <p className="text-gray-500">Aucune transaction</p>
          </Card>
        ) : (
          <div className="space-y-2">
            {filteredTransactions.map((transaction) => (
              <div
                key={transaction.id}
                onClick={() => router.push(`/history/${transaction.id}`)}
              >
                <TransactionItem transaction={transaction} />
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

