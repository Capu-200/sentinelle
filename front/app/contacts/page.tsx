'use client';

import { GlassCard } from "@/components/ui/glass-card";
import { ArrowLeft, Plus, Search, User } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function ContactsPage() {
    // Mock Contacts
    const contacts = [
        { id: 1, name: "Alice Martin", initials: "AM", color: "bg-pink-100 text-pink-600" },
        { id: 2, name: "Bob Wilson", initials: "BW", color: "bg-blue-100 text-blue-600" },
        { id: 3, name: "Charlie Davis", initials: "CD", color: "bg-green-100 text-green-600" },
        { id: 4, name: "David Miller", initials: "DM", color: "bg-orange-100 text-orange-600" },
    ];

    const [searchTerm, setSearchTerm] = useState("");
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [newContactName, setNewContactName] = useState("");
    const [modalStep, setModalStep] = useState(1); // 1: Input, 2: Success

    const filteredContacts = contacts.filter(c =>
        c.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleAddContact = () => {
        // validate
        if (!newContactName.trim()) return;

        // Simulate API call
        setTimeout(() => {
            setModalStep(2);
            setTimeout(() => {
                setIsAddModalOpen(false);
                setModalStep(1);
                // In a real app, we would re-fetch data here
                setNewContactName("");
            }, 1500);
        }, 800);
    };

    return (
        <div className="max-w-2xl mx-auto space-y-6 pb-20 relative">
            {/* Add Contact Modal Overlay */}
            {isAddModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-white dark:bg-slate-900 w-full max-w-sm rounded-3xl p-6 shadow-2xl space-y-6 animate-in zoom-in-95 duration-200">
                        {modalStep === 1 ? (
                            <>
                                <div className="space-y-2 text-center">
                                    <h3 className="text-xl font-bold">Nouveau bénéficiaire</h3>
                                    <p className="text-sm text-muted-foreground">Entrez les informations du contact</p>
                                </div>

                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium ml-1">Nom complet</label>
                                        <input
                                            autoFocus
                                            type="text"
                                            value={newContactName}
                                            onChange={e => setNewContactName(e.target.value)}
                                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
                                            placeholder="Ex: Marie Curie"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium ml-1">IBAN</label>
                                        <input
                                            type="text"
                                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm uppercase"
                                            placeholder="FR76 ...."
                                            defaultValue="FR76 3000 1007 2843 3812 3456 123"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-3 pt-2">
                                    <button
                                        onClick={() => setIsAddModalOpen(false)}
                                        className="py-3 rounded-xl font-bold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                    >
                                        Annuler
                                    </button>
                                    <button
                                        onClick={handleAddContact}
                                        disabled={!newContactName.trim()}
                                        className="py-3 rounded-xl font-bold bg-indigo-600 text-white shadow-lg shadow-indigo-500/20 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                    >
                                        Ajouter
                                    </button>
                                </div>
                            </>
                        ) : (
                            <div className="py-8 flex flex-col items-center gap-4 text-center">
                                <div className="h-16 w-16 rounded-full bg-green-100 text-green-600 flex items-center justify-center mb-2 animate-bounce">
                                    <User className="h-8 w-8" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-green-600">Contact ajouté !</h3>
                                    <p className="text-sm text-muted-foreground mt-1">{newContactName}</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="flex items-center gap-4">
                <Link href="/" className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                    <ArrowLeft className="h-6 w-6" />
                </Link>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold">Mes Contacts</h1>
                    <p className="text-sm text-muted-foreground">Gérez vos bénéficiaires</p>
                </div>
                <button
                    onClick={() => setIsAddModalOpen(true)}
                    className="p-2 bg-indigo-600 text-white rounded-xl shadow-lg shadow-indigo-500/20 hover:bg-indigo-700 transition-colors active:scale-95"
                >
                    <Plus className="h-6 w-6" />
                </button>
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                    type="text"
                    placeholder="Rechercher un contact..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border-none bg-white dark:bg-slate-900 shadow-sm ring-1 ring-slate-200 dark:ring-slate-800 focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                />
            </div>

            {/* Contacts Lists */}
            <div className="space-y-4">
                {filteredContacts.map(contact => (
                    <GlassCard key={contact.id} className="flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer group">
                        <div className="flex items-center gap-4">
                            <div className={`h-12 w-12 rounded-full flex items-center justify-center font-bold text-sm ${contact.color}`}>
                                {contact.initials}
                            </div>
                            <div>
                                <p className="font-semibold">{contact.name}</p>
                                <p className="text-xs text-muted-foreground">IBAN •••• 4242</p>
                            </div>
                        </div>
                        <Link href={`/transfer?to=${contact.id}`} className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-bold rounded-lg group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                            Envoyer
                        </Link>
                    </GlassCard>
                ))}

                {filteredContacts.length === 0 && (
                    <div className="text-center py-12 text-muted-foreground">
                        <User className="h-12 w-12 mx-auto mb-4 opacity-20" />
                        <p>Aucun contact trouvé</p>
                    </div>
                )}
            </div>
        </div>
    );
}
