"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Send, HandCoins } from "lucide-react";
import { cn } from "@/lib/utils";

interface Contact {
  name: string;
  email?: string;
  iban?: string;
  is_internal: boolean;
}

export function ContactHomeItem({ contact }: { contact: Contact }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  const target = contact.email || contact.iban;

  return (
    <div className="relative" ref={menuRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex flex-col items-center gap-2 min-w-[64px] group focus:outline-none"
      >
        <div className={cn("h-16 w-16 rounded-2xl flex items-center justify-center font-bold text-xl shadow-sm group-hover:scale-105 group-hover:shadow-md transition-all",
          contact.is_internal ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400" : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
          isOpen && "ring-2 ring-indigo-500 scale-105"
        )}>
          {contact.name.split(' ').slice(0, 2).map((n: string) => n[0]).join('').toUpperCase()}
        </div>
        <span className={cn("text-xs font-medium transition-colors truncate max-w-[64px]", isOpen ? "text-indigo-600" : "text-slate-600 dark:text-slate-300 group-hover:text-indigo-600")}>
          {contact.name.split(' ')[0]}
        </span>
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Modal Content */}
          <div 
            ref={menuRef}
            className="relative bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-2xl rounded-3xl p-6 flex flex-col items-center gap-4 w-full max-w-xs animate-in zoom-in-95 duration-200"
          >
            <div className={cn("h-20 w-20 rounded-2xl flex items-center justify-center font-bold text-2xl mb-2",
              contact.is_internal ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400" : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
            )}>
              {contact.name.split(' ').slice(0, 2).map((n: string) => n[0]).join('').toUpperCase()}
            </div>
            
            <div className="text-center mb-2">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">{contact.name}</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 truncate max-w-[200px]">{contact.email || contact.iban}</p>
            </div>

            <div className="flex flex-col gap-2 w-full">
              <Link 
                href={`/transfer?to=${target}`}
                className="flex items-center justify-between w-full px-5 py-4 font-semibold rounded-2xl bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-500/10 dark:hover:bg-indigo-500/20 text-indigo-700 dark:text-indigo-400 transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <span>Envoyer de l'argent</span>
                <Send className="h-5 w-5" />
              </Link>
              <Link 
                href={`/request?to=${target}`}
                className="flex items-center justify-between w-full px-5 py-4 font-semibold rounded-2xl bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-500/10 dark:hover:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <span>Demander des fonds</span>
                <HandCoins className="h-5 w-5" />
              </Link>
            </div>
            
            <button 
              onClick={() => setIsOpen(false)}
              className="mt-2 text-sm font-semibold text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              Annuler
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
