'use client';

import { useEffect } from 'react';
import Badge from './ui/Badge';

interface NotificationProps {
  message: string;
  type?: 'success' | 'warning' | 'error' | 'info';
  onClose: () => void;
  duration?: number;
}

export default function Notification({
  message,
  type = 'info',
  onClose,
  duration = 5000,
}: NotificationProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);
  
  const icons = {
    success: '✅',
    warning: '⚠️',
    error: '❌',
    info: 'ℹ️',
  };
  
  const bgColors = {
    success: 'bg-green-50 border-green-200',
    warning: 'bg-yellow-50 border-yellow-200',
    error: 'bg-red-50 border-red-200',
    info: 'bg-blue-50 border-blue-200',
  };
  
  return (
    <div className={`fixed top-4 left-4 right-4 max-w-md mx-auto z-50 animate-slide-down`}>
      <div className={`${bgColors[type]} border rounded-xl p-4 shadow-lg flex items-start gap-3`}>
        <span className="text-2xl">{icons[type]}</span>
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">{message}</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

