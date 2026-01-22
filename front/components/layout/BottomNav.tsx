'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { HomeIcon, ClipboardDocumentListIcon, UserIcon } from '@heroicons/react/24/outline';
import { HomeIcon as HomeIconSolid, ClipboardDocumentListIcon as ClipboardDocumentListIconSolid, UserIcon as UserIconSolid } from '@heroicons/react/24/solid';

export default function BottomNav() {
  const pathname = usePathname();
  
  const navItems = [
    { 
      href: '/', 
      label: 'Accueil', 
      Icon: HomeIcon, 
      IconSolid: HomeIconSolid 
    },
    { 
      href: '/history', 
      label: 'Historique', 
      Icon: ClipboardDocumentListIcon, 
      IconSolid: ClipboardDocumentListIconSolid 
    },
    { 
      href: '/profile', 
      label: 'Profil', 
      Icon: UserIcon, 
      IconSolid: UserIconSolid 
    },
  ];
  
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-area-bottom">
      <div className="flex justify-around items-center h-16 max-w-md mx-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const IconComponent = isActive ? item.IconSolid : item.Icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                isActive ? 'text-orange-500' : 'text-gray-500'
              }`}
            >
              <IconComponent className="w-6 h-6 mb-1" />
              <span className="text-xs font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

