'use client';

import { useEffect } from 'react';
import Badge from './ui/Badge';
import { CheckCircleIcon, ExclamationTriangleIcon, XCircleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

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
    success: CheckCircleIcon,
    warning: ExclamationTriangleIcon,
    error: XCircleIcon,
    info: InformationCircleIcon,
  };
  
  const bgColors = {
    success: 'bg-green-50 border-green-200',
    warning: 'bg-yellow-50 border-yellow-200',
    error: 'bg-red-50 border-red-200',
    info: 'bg-blue-50 border-blue-200',
  };
  
  const IconComponent = icons[type];
  
  return (
    <div className={`fixed top-4 left-4 right-4 max-w-md mx-auto z-50 animate-slide-down`}>
      <div className={`${bgColors[type]} border rounded-xl p-4 shadow-lg flex items-start gap-3`}>
        <IconComponent className={`w-6 h-6 flex-shrink-0 ${
          type === 'success' ? 'text-green-600' :
          type === 'warning' ? 'text-yellow-600' :
          type === 'error' ? 'text-red-600' :
          'text-blue-600'
        }`} />
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">{message}</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 flex-shrink-0"
        >
          <XCircleIcon className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}

