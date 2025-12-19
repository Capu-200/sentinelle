'use client';

import { useState } from 'react';
import { mockProfile } from '@/lib/mock-data';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';

export default function ProfilePage() {
  const [profile] = useState(mockProfile);
  
  const getKYCStatus = (status: typeof profile.kycStatus) => {
    switch (status) {
      case 'verified':
        return {
          badge: <Badge variant="success">Vérifié</Badge>,
          message: 'Votre identité a été vérifiée',
        };
      case 'pending':
        return {
          badge: <Badge variant="warning">En attente</Badge>,
          message: 'Vérification en cours',
        };
      case 'unverified':
        return {
          badge: <Badge variant="error">Non vérifié</Badge>,
          message: 'Vérification requise',
        };
    }
  };
  
  const kycInfo = getKYCStatus(profile.kycStatus);
  
  return (
    <div className="min-h-screen pb-20">
      <header className="sticky top-0 z-10 bg-white border-b border-gray-100 px-4 py-4">
        <h1 className="text-xl font-bold text-gray-900">Profil</h1>
      </header>
      
      <main className="px-4 py-6 space-y-6">
        {/* Profile Header */}
        <Card className="text-center py-6">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-orange-400 to-blue-400 flex items-center justify-center text-white text-2xl font-semibold mx-auto mb-4">
            {profile.name.charAt(0)}
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-1">{profile.name}</h2>
          <p className="text-sm text-gray-500">{profile.email}</p>
        </Card>
        
        {/* KYC Status */}
        <Card>
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-900">Vérification d'identité</h3>
            {kycInfo.badge}
          </div>
          <p className="text-sm text-gray-600 mb-4">{kycInfo.message}</p>
          {profile.kycStatus !== 'verified' && (
            <Button variant="primary" size="sm" className="w-full">
              Compléter la vérification
            </Button>
          )}
        </Card>
        
        {/* Payment Methods */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-3">Moyens de paiement</h3>
          <div className="space-y-2">
            {profile.paymentMethods.map((method) => (
              <Card key={method.id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-100 to-blue-100 flex items-center justify-center">
                    {method.type === 'iban' ? '🏦' : '💳'}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">{method.label}</div>
                    <div className="text-xs text-gray-500">
                      {method.type === 'iban' ? 'Compte bancaire' : 'Carte bancaire'}
                    </div>
                  </div>
                </div>
                <button className="text-gray-400">→</button>
              </Card>
            ))}
          </div>
          <Button variant="outline" size="md" className="w-full mt-3">
            Ajouter un moyen de paiement
          </Button>
        </div>
        
        {/* Security Settings */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-3">Sécurité</h3>
          <Card className="space-y-4">
            <button className="flex items-center justify-between w-full text-left">
              <div>
                <div className="font-semibold text-gray-900">Code PIN</div>
                <div className="text-sm text-gray-500">Modifier votre code PIN</div>
              </div>
              <span className="text-gray-400">→</span>
            </button>
            
            <div className="border-t border-gray-100 pt-4">
              <button className="flex items-center justify-between w-full text-left">
                <div>
                  <div className="font-semibold text-gray-900">Authentification à deux facteurs</div>
                  <div className="text-sm text-gray-500">Activer la 2FA</div>
                </div>
                <span className="text-gray-400">→</span>
              </button>
            </div>
            
            <div className="border-t border-gray-100 pt-4">
              <button className="flex items-center justify-between w-full text-left">
                <div>
                  <div className="font-semibold text-gray-900">Notifications de sécurité</div>
                  <div className="text-sm text-gray-500">Gérer les alertes</div>
                </div>
                <span className="text-gray-400">→</span>
              </button>
            </div>
          </Card>
        </div>
        
        {/* GDPR & Data */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-3">Données personnelles</h3>
          <Card className="space-y-4">
            <button className="flex items-center justify-between w-full text-left">
              <div>
                <div className="font-semibold text-gray-900">Exporter mes données</div>
                <div className="text-sm text-gray-500">Télécharger une copie de vos données</div>
              </div>
              <span className="text-gray-400">→</span>
            </button>
            
            <div className="border-t border-gray-100 pt-4">
              <button className="flex items-center justify-between w-full text-left text-red-600">
                <div>
                  <div className="font-semibold">Supprimer mon compte</div>
                  <div className="text-sm opacity-75">Supprimer définitivement votre compte</div>
                </div>
                <span className="text-red-400">→</span>
              </button>
            </div>
          </Card>
        </div>
        
        {/* App Info */}
        <div className="text-center text-xs text-gray-400 py-4">
          <p>Sentinelle v1.0.0</p>
          <p className="mt-1">Sécurisé par intelligence artificielle</p>
        </div>
      </main>
    </div>
  );
}

