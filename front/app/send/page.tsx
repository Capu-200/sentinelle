'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { mockContacts } from '@/lib/mock-data';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Skeleton from '@/components/ui/Skeleton';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

type Step = 'contact' | 'amount' | 'confirm' | 'processing';

export default function SendPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const contactParam = searchParams.get('contact');
  const [step, setStep] = useState<Step>(contactParam ? 'amount' : 'contact');
  const [selectedContact, setSelectedContact] = useState<string | null>(contactParam);
  const [amount, setAmount] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [transactionStatus, setTransactionStatus] = useState<'validated' | 'verifying' | 'blocked' | null>(null);
  
  const contact = selectedContact ? mockContacts.find(c => c.id === selectedContact) : null;
  
  const handleContactSelect = (contactId: string) => {
    setSelectedContact(contactId);
    setStep('amount');
  };
  
  const handleAmountSubmit = () => {
    if (parseFloat(amount) > 0) {
      setStep('confirm');
    }
  };
  
  const handleConfirm = async () => {
    setIsProcessing(true);
    setStep('processing');
    
    // Simuler le traitement par l'IA
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Simuler différents résultats (80% validé, 15% vérification, 5% bloqué)
    const random = Math.random();
    if (random < 0.8) {
      setTransactionStatus('validated');
    } else if (random < 0.95) {
      setTransactionStatus('verifying');
      router.push(`/verify?amount=${amount}&contact=${selectedContact}`);
      return;
    } else {
      setTransactionStatus('blocked');
    }
    
    setIsProcessing(false);
  };
  
  const handleFinish = () => {
    router.push('/');
  };
  
  return (
    <div className="min-h-screen pb-20">
      <main className="px-4 py-6">
        {/* Step Indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {['contact', 'amount', 'confirm'].map((s, i) => (
            <div key={s} className="flex items-center">
              <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                  step === s || (step === 'processing' && i < 3)
                    ? 'bg-gradient-to-r from-orange-500 to-blue-500 text-white'
                    : step !== 'contact' && ['amount', 'confirm'].indexOf(step) > i
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {step !== 'contact' && ['amount', 'confirm'].indexOf(step) > i ? '✓' : i + 1}
              </div>
              {i < 2 && (
                <div
                  className={`w-12 h-1 ${
                    step !== 'contact' && ['amount', 'confirm'].indexOf(step) > i
                      ? 'bg-green-500'
                      : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        
        {/* Step 1: Select Contact */}
        {step === 'contact' && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Sélectionner un contact</h2>
            
            {/* Favorites */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Favoris</h3>
              <div className="space-y-2">
                {mockContacts
                  .filter(c => c.isFavorite)
                  .map((contact) => (
                    <Card
                      key={contact.id}
                      onClick={() => handleContactSelect(contact.id)}
                      className="flex items-center gap-3"
                    >
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-400 to-blue-400 flex items-center justify-center text-white font-semibold">
                        {contact.name.charAt(0)}
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{contact.name}</div>
                      </div>
                      <span className="text-gray-400">→</span>
                    </Card>
                  ))}
              </div>
            </div>
            
            {/* All Contacts */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Tous les contacts</h3>
              <div className="space-y-2">
                {mockContacts
                  .filter(c => !c.isFavorite)
                  .map((contact) => (
                    <Card
                      key={contact.id}
                      onClick={() => handleContactSelect(contact.id)}
                      className="flex items-center gap-3"
                    >
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-400 to-blue-400 flex items-center justify-center text-white font-semibold">
                        {contact.name.charAt(0)}
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{contact.name}</div>
                      </div>
                      <span className="text-gray-400">→</span>
                    </Card>
                  ))}
              </div>
            </div>
          </div>
        )}
        
        {/* Step 2: Enter Amount */}
        {step === 'amount' && contact && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-orange-400 to-blue-400 flex items-center justify-center text-white text-2xl font-semibold mx-auto mb-4">
                {contact.name.charAt(0)}
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-1">{contact.name}</h2>
            </div>
            
            <Card className="text-center py-8">
              <label className="block text-sm text-gray-500 mb-2">Montant</label>
              <div className="flex items-center justify-center gap-2">
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  className="text-4xl font-bold text-gray-900 text-center border-none outline-none w-full"
                  autoFocus
                />
                <span className="text-2xl text-gray-500">€</span>
              </div>
            </Card>
            
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={handleAmountSubmit}
              disabled={!amount || parseFloat(amount) <= 0}
            >
              Continuer
            </Button>
          </div>
        )}
        
        {/* Step 3: Confirm */}
        {step === 'confirm' && contact && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-gray-900 text-center">Confirmer la transaction</h2>
            
            <Card className="space-y-4">
              <div className="flex items-center gap-3 pb-4 border-b border-gray-100">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-400 to-blue-400 flex items-center justify-center text-white font-semibold">
                  {contact.name.charAt(0)}
                </div>
                <div className="flex-1">
                  <div className="text-sm text-gray-500">Destinataire</div>
                  <div className="font-semibold text-gray-900">{contact.name}</div>
                </div>
              </div>
              
              <div>
                <div className="text-sm text-gray-500 mb-1">Montant</div>
                <div className="text-3xl font-bold text-gray-900">{parseFloat(amount).toFixed(2)} €</div>
              </div>
            </Card>
            
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={handleConfirm}
            >
              Envoyer
            </Button>
          </div>
        )}
        
        {/* Step 4: Processing */}
        {step === 'processing' && (
          <div className="space-y-6 text-center py-12">
            <div className="w-20 h-20 mx-auto mb-4">
              <div className="w-full h-full border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Traitement en cours...</h2>
            <p className="text-gray-500">Vérification de sécurité par IA</p>
          </div>
        )}
        
        {/* Transaction Result */}
        {transactionStatus === 'validated' && (
          <div className="space-y-6 text-center py-12">
            <div className="w-20 h-20 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircleIcon className="w-12 h-12 text-green-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Transaction validée</h2>
            <p className="text-gray-500">
              {amount} € ont été envoyés à {contact?.name}
            </p>
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={handleFinish}
            >
              Retour à l'accueil
            </Button>
          </div>
        )}
        
        {transactionStatus === 'blocked' && (
          <div className="space-y-6 text-center py-12">
            <div className="w-20 h-20 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
              <XCircleIcon className="w-12 h-12 text-red-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Transaction bloquée</h2>
            <p className="text-gray-500 mb-4">
              Cette transaction a été bloquée pour votre sécurité.
            </p>
            <Card className="text-left">
              <p className="text-sm text-gray-600">
                Si vous pensez qu'il s'agit d'une erreur, contactez notre support.
              </p>
            </Card>
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={handleFinish}
            >
              Retour à l'accueil
            </Button>
          </div>
        )}
      </main>
    </div>
  );
}

