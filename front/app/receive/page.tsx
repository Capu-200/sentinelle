'use client';

import { useState } from 'react';
import Link from 'next/link';
import { GlassCard } from '@/components/ui/glass-card';
import { ArrowLeft, Copy, Check, Share2, QrCode } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ReceivePage() {
  const [copied, setCopied] = useState(false);

  // In a real app, this would be dynamic
  const qrCodeUrl = 'https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=PAYON-USER-JACQUES-123';
  const paymentLink = 'payon.app/pay/jacques';

  const handleCopy = () => {
    navigator.clipboard.writeText(paymentLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Recevoir avec PayOn',
          text: `Envoyez-moi de l'argent instantanément sur PayOn : ${paymentLink}`,
          url: `https://${paymentLink}`,
        });
      } catch (err) {
        console.error('Share failed:', err);
      }
    } else {
      handleCopy();
    }
  };

  return (
    <div className="flex min-h-[80vh] flex-col max-w-md mx-auto lg:max-w-xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/" className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
          <ArrowLeft className="h-6 w-6" />
        </Link>
        <h1 className="text-xl font-bold">Recevoir des fonds</h1>
      </div>

      <div className="space-y-6">
        <GlassCard className="p-8 text-center flex flex-col items-center gap-6">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
            <div className="relative bg-white p-4 rounded-xl">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={qrCodeUrl}
                alt="Votre QR Code PayOn"
                className="w-48 h-48 mix-blend-multiply dark:mix-blend-normal"
              />
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-lg font-bold">Jacques Dupont</h2>
            <p className="text-sm text-muted-foreground">Scannez pour m'envoyer de l'argent</p>
          </div>

          {/* Link & Actions */}
          <div className="w-full space-y-3">
            <div
              onClick={handleCopy}
              className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 cursor-pointer hover:border-indigo-500 transition-colors group"
            >
              <span className="text-sm font-medium text-slate-600 dark:text-slate-300 font-mono truncate px-2">
                {paymentLink}
              </span>
              <div className="p-2 rounded-lg bg-white dark:bg-slate-800 shadow-sm text-indigo-600 group-hover:scale-105 transition-transform">
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </div>
            </div>

            <button
              onClick={handleShare}
              className="flex items-center justify-center gap-2 w-full py-3.5 rounded-xl bg-indigo-600 text-white font-bold shadow-lg shadow-indigo-500/25 hover:bg-indigo-700 active:scale-95 transition-all"
            >
              <Share2 className="h-4 w-4" />
              <span>Partager mon lien</span>
            </button>
          </div>
        </GlassCard>

        {/* Instructions */}
        <div className="px-4 py-2">
          <h3 className="text-sm font-medium text-muted-foreground mb-4 uppercase tracking-wider text-xs">Comment ça marche ?</h3>
          <div className="space-y-4">
            <div className="flex gap-4">
              <div className="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 flex items-center justify-center font-bold text-sm shrink-0">1</div>
              <p className="text-sm text-slate-600 dark:text-slate-400 pt-1.5">Partagez votre QR code ou votre lien unique à votre contact.</p>
            </div>
            <div className="flex gap-4">
              <div className="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 flex items-center justify-center font-bold text-sm shrink-0">2</div>
              <p className="text-sm text-slate-600 dark:text-slate-400 pt-1.5">Il scanne ou clique pour ouvrir l'interface de paiement sécurisée.</p>
            </div>
            <div className="flex gap-4">
              <div className="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 flex items-center justify-center font-bold text-sm shrink-0">3</div>
              <p className="text-sm text-slate-600 dark:text-slate-400 pt-1.5">Vous recevez les fonds instantanément sur votre compte PayOn.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

