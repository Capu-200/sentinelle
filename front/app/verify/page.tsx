
import { Suspense } from 'react';
import VerifyClient from '@/app/verify/verify-client';

export default function VerifyPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Chargement de la vérification…</div>}>
      <VerifyClient />
    </Suspense>
  );
}

