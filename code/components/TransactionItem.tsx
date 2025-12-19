import { Transaction } from '@/types';
import Badge from './ui/Badge';

interface TransactionItemProps {
  transaction: Transaction;
  onClick?: () => void;
}

export default function TransactionItem({ transaction, onClick }: TransactionItemProps) {
  const formatAmount = (amount: number, type: string) => {
    const sign = type === 'sent' ? '-' : '+';
    return `${sign}${amount.toFixed(2)} €`;
  };
  
  const getStatusBadge = (status: Transaction['status']) => {
    switch (status) {
      case 'validated':
        return <Badge variant="success">Validée</Badge>;
      case 'pending':
        return <Badge variant="warning">En attente</Badge>;
      case 'verifying':
        return <Badge variant="info">Vérification</Badge>;
      case 'blocked':
        return <Badge variant="error">Bloquée</Badge>;
    }
  };
  
  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (minutes < 1) return 'À l\'instant';
    if (minutes < 60) return `Il y a ${minutes} min`;
    if (hours < 24) return `Il y a ${hours}h`;
    if (days < 7) return `Il y a ${days}j`;
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  };
  
  return (
    <div
      className="flex items-center justify-between p-4 bg-white rounded-xl border border-gray-100 mb-2 cursor-pointer hover:bg-gray-50 transition-all duration-200 active:scale-[0.98]"
      onClick={onClick}
    >
      <div className="flex items-center gap-3 flex-1">
        <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl ${
          transaction.type === 'sent' ? 'bg-red-100' : 'bg-green-100'
        }`}>
          {transaction.type === 'sent' ? '📤' : '📥'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-gray-900 truncate">
            {transaction.type === 'sent' ? transaction.recipient : transaction.sender}
          </div>
          <div className="text-sm text-gray-500">{formatDate(transaction.date)}</div>
        </div>
      </div>
      <div className="flex flex-col items-end gap-1">
        <div className={`font-bold text-lg ${
          transaction.type === 'sent' ? 'text-gray-900' : 'text-green-600'
        }`}>
          {formatAmount(transaction.amount, transaction.type)}
        </div>
        {getStatusBadge(transaction.status)}
      </div>
    </div>
  );
}

