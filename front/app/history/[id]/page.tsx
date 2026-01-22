'use client';

import { use } from 'react';
import { useRouter } from 'next/navigation';
import { mockTransactions } from '@/lib/mock-data';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { XCircleIcon, CheckCircleIcon, ClockIcon, LockClosedIcon, ShieldExclamationIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

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
          <XCircleIcon className="w-16 h-16 mx-auto mb-4 text-red-500" />
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
          Icon: CheckCircleIcon,
          message: 'Transaction validée et traitée avec succès',
        };
      case 'pending':
        return {
          badge: <Badge variant="warning">En attente</Badge>,
          Icon: ClockIcon,
          message: 'Transaction en cours de traitement',
        };
      case 'verifying':
        return {
          badge: <Badge variant="info">Vérification</Badge>,
          Icon: LockClosedIcon,
          message: 'Transaction en cours de vérification par notre système de sécurité',
        };
      case 'blocked':
        return {
          badge: <Badge variant="error">Bloquée</Badge>,
          Icon: ShieldExclamationIcon,
          message: transaction.reason || 'Transaction bloquée pour votre sécurité',
        };
    }
  };
  
  const statusInfo = getStatusInfo(transaction.status);
  const StatusIcon = statusInfo.Icon;
  
  return (
    <div className="min-h-screen pb-20">
      <main className="px-4 py-6 space-y-4">
        {/* Status Card */}
        <Card className="text-center py-8 bg-gradient-to-br from-orange-50 via-white to-blue-50">
          <div className="flex justify-center mb-4">
            <StatusIcon className={`w-16 h-16 ${
              transaction.status === 'validated' ? 'text-green-600' :
              transaction.status === 'pending' ? 'text-yellow-600' :
              transaction.status === 'verifying' ? 'text-blue-600' :
              'text-red-600'
            }`} />
          </div>
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
              <InformationCircleIcon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
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

