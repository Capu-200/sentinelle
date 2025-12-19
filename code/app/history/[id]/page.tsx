'use client';

import { use } from 'react';
import { useRouter } from 'next/navigation';
import { mockTransactions } from '@/lib/mock-data';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';

export default function TransactionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { id } = use(params);
  const transaction = mockTransactions.find(t => t.id === id);
  
  if (!transaction) {
    return (
      <div className="min-h-screen pb-20 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">❌</div>
          <p className="text-gray-500">Transaction introuvable</p>
          <Button
            variant="primary"
            className="mt-4"
            onClick={() => router.push('/history')}
          >
            Retour
          </Button>
        </div>
      </div>
    );
  }
  
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  const getStatusInfo = (status: typeof transaction.status) => {
    switch (status) {
      case 'validated':
        return {
          badge: <Badge variant="success">Validée</Badge>,
          icon: '✅',
          message: 'Transaction validée et traitée avec succès',
        };
      case 'pending':
        return {
          badge: <Badge variant="warning">En attente</Badge>,
          icon: '⏳',
          message: 'Transaction en cours de traitement',
        };
      case 'verifying':
        return {
          badge: <Badge variant="info">Vérification</Badge>,
          icon: '🔒',
          message: 'Transaction en cours de vérification par notre système de sécurité',
        };
      case 'blocked':
        return {
          badge: <Badge variant="error">Bloquée</Badge>,
          icon: '🚫',
          message: transaction.reason || 'Transaction bloquée pour votre sécurité',
        };
    }
  };
  
  const statusInfo = getStatusInfo(transaction.status);
  
  return (
    <div className="min-h-screen pb-20">
      <header className="sticky top-0 z-10 bg-white border-b border-gray-100 px-4 py-4">
        <button
          onClick={() => router.back()}
          className="text-gray-600 text-xl"
        >
          ←
        </button>
        <h1 className="text-xl font-bold text-gray-900 mt-2">Détails de la transaction</h1>
      </header>
      
      <main className="px-4 py-6 space-y-4">
        {/* Status Card */}
        <Card className="text-center py-8 bg-gradient-to-br from-orange-50 via-white to-blue-50">
          <div className="text-5xl mb-4">{statusInfo.icon}</div>
          <div className="mb-2">{statusInfo.badge}</div>
          <div className={`text-3xl font-bold mb-2 ${
            transaction.type === 'sent' ? 'text-gray-900' : 'text-green-600'
          }`}>
            {transaction.type === 'sent' ? '-' : '+'}{transaction.amount.toFixed(2)} €
          </div>
          <p className="text-sm text-gray-500">{statusInfo.message}</p>
        </Card>
        
        {/* Details */}
        <Card className="space-y-4">
          <div>
            <div className="text-sm text-gray-500 mb-1">
              {transaction.type === 'sent' ? 'Destinataire' : 'Expéditeur'}
            </div>
            <div className="font-semibold text-gray-900">
              {transaction.type === 'sent' ? transaction.recipient : transaction.sender}
            </div>
          </div>
          
          <div className="border-t border-gray-100 pt-4">
            <div className="text-sm text-gray-500 mb-1">Date</div>
            <div className="font-semibold text-gray-900">{formatDate(transaction.date)}</div>
          </div>
          
          <div className="border-t border-gray-100 pt-4">
            <div className="text-sm text-gray-500 mb-1">Type</div>
            <div className="font-semibold text-gray-900">
              {transaction.type === 'sent' ? 'Envoi' : 'Réception'}
            </div>
          </div>
          
          <div className="border-t border-gray-100 pt-4">
            <div className="text-sm text-gray-500 mb-1">ID de transaction</div>
            <div className="font-mono text-xs text-gray-600 break-all">{transaction.id}</div>
          </div>
        </Card>
        
        {/* Blocked Transaction Info */}
        {transaction.status === 'blocked' && (
          <Card className="bg-red-50 border-red-200">
            <div className="flex items-start gap-3">
              <span className="text-xl">ℹ️</span>
              <div className="flex-1">
                <p className="font-semibold text-gray-900 mb-1">Transaction bloquée</p>
                <p className="text-sm text-gray-600 mb-3">
                  {transaction.reason || 'Cette transaction a été bloquée par notre système de sécurité.'}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    alert('Support: contactez-nous à support@sentinelle.app');
                  }}
                >
                  Contacter le support
                </Button>
              </div>
            </div>
          </Card>
        )}
        
        {/* Actions */}
        <div className="pt-4">
          <Button
            variant="outline"
            size="lg"
            className="w-full"
            onClick={() => {
              // Simuler l'export
              alert('Export de la transaction en PDF...');
            }}
          >
            Exporter en PDF
          </Button>
        </div>
      </main>
    </div>
  );
}

