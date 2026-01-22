'use client';

import { useState } from 'react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';

export default function ReceivePage() {
  const [copied, setCopied] = useState(false);
  
  const qrCode = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=SENTINELLE-USER-123';
  const paymentLink = 'sentinelle.app/pay/user123';
  
  const handleCopy = () => {
    navigator.clipboard.writeText(paymentLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <div className="min-h-screen pb-20">
      <main className="px-4 py-6 space-y-6">
        <Card className="text-center py-8">
          <div className="mb-6 animate-fade-in">
            <img
              src={qrCode}
              alt="QR Code"
              className="w-48 h-48 mx-auto border-4 border-gray-100 rounded-xl shadow-sm"
            />
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Scannez pour recevoir
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            Partagez ce code QR ou le lien ci-dessous
          </p>
          
          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm text-gray-600 truncate flex-1">{paymentLink}</span>
              <button
                onClick={handleCopy}
                className="text-orange-500 font-medium text-sm whitespace-nowrap"
              >
                {copied ? '✓ Copié' : 'Copier'}
              </button>
            </div>
          </div>
          
          <div className="flex gap-3">
            <Button
              variant="outline"
              size="md"
              className="flex-1"
              onClick={() => {
                // Simuler le partage
                if (navigator.share) {
                  navigator.share({
                    title: 'Recevez de l\'argent via Sentinelle',
                    text: `Envoyez-moi ${paymentLink}`,
                    url: paymentLink,
                  });
                }
              }}
            >
              Partager
            </Button>
          </div>
        </Card>
        
        <Card>
          <h3 className="font-semibold text-gray-900 mb-3">Comment ça marche ?</h3>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex items-start gap-3">
              <span className="text-orange-500 font-bold">1.</span>
              <p>Partagez votre code QR ou votre lien</p>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-orange-500 font-bold">2.</span>
              <p>Votre contact vous envoie l'argent</p>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-orange-500 font-bold">3.</span>
              <p>Vous recevez une notification instantanée</p>
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
}

