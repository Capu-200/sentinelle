import { Suspense } from 'react';
import SendClient from '@/app/send/send-client';

export default function SendPage() {
  return (
    <Suspense fallback={<div className="p-6 text-center">Chargement…</div>}>
      <SendClient />
    </Suspense>
  );
}