'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { mockContacts } from '@/lib/mock-data';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';

export default function VerifyPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const amount = searchParams.get('amount');
  const contactId = searchParams.get('contact');
  const [timeRemaining, setTimeRemaining] = useState(45); // secondes
  const [isVerifying, setIsVerifying] = useState(true);
  
  const contact = contactId ? mockContacts.find(c => c.id === contactId) : null;
  
  useEffect(() => {
    if (!isVerifying) return;
    
    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          setIsVerifying(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [isVerifying]);
  
  const handleConfirm = async () => {
    // Simuler la confirmation et la validation
    await new Promise(resolve => setTimeout(resolve, 1000));
    router.push(`/?status=validated&amount=${amount}&contact=${contactId}`);
  };
  
  const handleHelp = () => {
    // Simuler l'ouverture du support
    alert('Support: contactez-nous à support@sentinelle.app');
  };
  
  return (
    <div className="min-h-screen pb-20 bg-gradient-to-b from-orange-50 via-white to-blue-50">
      <header className="sticky top-0 z-10 bg-white/80 backdrop-blur-sm border-b border-gray-100 px-4 py-4">
        <h1 className="text-xl font-bold text-gray-900">Vérification de sécurité</h1>
      </header>
      
      <main className="px-4 py-8 space-y-6">
        {/* Main Message */}
        <div className="text-center py-8">
          <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-orange-100 to-blue-100 rounded-full flex items-center justify-center">
            <span className="text-5xl">🔒</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">
            Vérification en cours
          </h2>
          <p className="text-lg text-gray-600 max-w-sm mx-auto">
            Nous vérifions cette transaction pour garantir la sécurité de votre compte.
          </p>
        </div>
        
        {/* Transaction Details */}
        <Card className="space-y-4">
          <div className="flex items-center gap-3 pb-4 border-b border-gray-100">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-400 to-blue-400 flex items-center justify-center text-white font-semibold">
              {contact?.name.charAt(0) || '?'}
            </div>
            <div className="flex-1">
              <div className="text-sm text-gray-500">Destinataire</div>
              <div className="font-semibold text-gray-900">{contact?.name || 'Contact'}</div>
            </div>
          </div>
          
          <div>
            <div className="text-sm text-gray-500 mb-1">Montant</div>
            <div className="text-2xl font-bold text-gray-900">{amount} €</div>
          </div>
        </Card>
        
        {/* Progress Indicator */}
        {isVerifying && (
          <Card className="bg-gradient-to-r from-orange-50 to-blue-50 border-orange-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin" />
              <div className="flex-1">
                <div className="font-semibold text-gray-900 text-sm">Analyse par IA en cours...</div>
                <div className="text-xs text-gray-600">
                  Temps estimé : moins d'une minute
                </div>
              </div>
            </div>
            <div className="w-full bg-orange-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-orange-500 to-blue-500 h-full transition-all duration-1000 ease-linear"
                style={{ width: `${((45 - timeRemaining) / 45) * 100}%` }}
              />
            </div>
          </Card>
        )}
        
        {/* Success State */}
        {!isVerifying && (
          <Card className="bg-green-50 border-green-200">
            <div className="flex items-center gap-3">
              <span className="text-3xl">✅</span>
              <div>
                <div className="font-semibold text-gray-900">Transaction validée</div>
                <div className="text-sm text-gray-600">
                  Votre paiement a été approuvé et traité avec succès.
                </div>
              </div>
            </div>
          </Card>
        )}
        
        {/* Actions */}
        <div className="space-y-3 pt-4">
          {isVerifying ? (
            <>
              <Button
                variant="primary"
                size="lg"
                className="w-full"
                onClick={handleConfirm}
              >
                Je confirme cette transaction
              </Button>
              <Button
                variant="outline"
                size="md"
                className="w-full"
                onClick={handleHelp}
              >
                Demander de l'aide
              </Button>
            </>
          ) : (
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={() => router.push('/')}
            >
              Retour à l'accueil
            </Button>
          )}
        </div>
        
        {/* Reassurance Message */}
        <Card className="bg-gray-50">
          <div className="flex items-start gap-3">
            <span className="text-xl">💡</span>
            <div className="text-sm text-gray-600">
              <p className="font-medium text-gray-900 mb-1">Pourquoi cette vérification ?</p>
              <p>
                Notre système de sécurité détecte automatiquement les transactions inhabituelles pour protéger votre compte. C'est normal et cela ne prend que quelques secondes.
              </p>
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
}

