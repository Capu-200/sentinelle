'use client';

import { GlassCard } from "@/components/ui/glass-card";
import { Plus, Search, User, Trash2, CheckCircle2, AlertCircle } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { addContactAction, deleteContactAction } from "@/app/actions/contacts";
import { useRouter } from "next/navigation";
import { toast } from "react-hot-toast";

interface Contact {
    contact_id: string;
    name: string;
    email?: string;
    iban?: string;
    initials: string;
    is_internal: boolean;
}

interface Props {
    initialContacts: Contact[];
}

export function ContactList({ initialContacts }: Props) {
    const router = useRouter();
    const [contacts, setContacts] = useState<Contact[]>(initialContacts);
    const [searchTerm, setSearchTerm] = useState("");

    // Modal State
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [newContactName, setNewContactName] = useState("");
    const [newContactEmail, setNewContactEmail] = useState("");
    const [newContactIban, setNewContactIban] = useState("");
    const [modalStep, setModalStep] = useState(1); // 1: Input, 2: Success
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");

    const filteredContacts = contacts.filter(c =>
        c.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleAddContact = async () => {
        setError("");
        if (!newContactName.trim()) return;
        if (!newContactEmail.trim() && !newContactIban.trim()) {
            setError("Veuillez saisir un email ou un IBAN");
            return;
        }

        setIsSubmitting(true);
        const formData = new FormData();
        formData.append("name", newContactName);
        if (newContactEmail) formData.append("email", newContactEmail);
        if (newContactIban) formData.append("iban", newContactIban);

        const res = await addContactAction(formData);

        setIsSubmitting(false);

        if (res.success) {
            setModalStep(2);
            router.refresh();
            // Optimistic update handled by page refresh or could push to state
            setTimeout(() => {
                setIsAddModalOpen(false);
                setModalStep(1);
                setNewContactName("");
                setNewContactEmail("");
                setNewContactIban("");
            }, 1500);
        } else {
            setError(res.error || "Erreur lors de l'ajout");
        }
    };

    const handleDelete = async (e: React.MouseEvent, id: string) => {
        e.preventDefault(); // Prevent navigation
        if (!confirm("Voulez-vous supprimer ce contact ?")) return;

        const res = await deleteContactAction(id);
        if (res.success) {
            router.refresh();
        } else {
            alert("Erreur lors de la suppression");
        }
    };

    return (
        <div className="space-y-6">
            {/* Add Contact Modal Overlay */}
            {isAddModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-white dark:bg-slate-900 w-full max-w-sm rounded-3xl p-6 shadow-2xl space-y-6 animate-in zoom-in-95 duration-200">
                        {modalStep === 1 ? (
                            <>
                                <div className="space-y-2 text-center">
                                    <h3 className="text-xl font-bold">Nouveau bénéficiaire</h3>
                                    <p className="text-sm text-muted-foreground">Ajouter un ami ou un compte externe</p>
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

                                    {/* Choice: Email OR Iban */}
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium ml-1">Email <span className="text-xs text-muted-foreground">(Pour virement interne)</span></label>
                                        <input
                                            type="email"
                                            value={newContactEmail}
                                            onChange={e => {
                                                setNewContactEmail(e.target.value);
                                                if (e.target.value) setNewContactIban(""); // Mutual exclusive logic for simplicity
                                            }}
                                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none outline-none focus:ring-2 focus:ring-indigo-500"
                                            placeholder="marie.curie@email.com"
                                            disabled={!!newContactIban}
                                        />
                                    </div>

                                    <div className="relative flex py-1 items-center">
                                        <div className="flex-grow border-t border-slate-200 dark:border-slate-700"></div>
                                        <span className="flex-shrink-0 mx-4 text-xs text-slate-400 font-medium">OU</span>
                                        <div className="flex-grow border-t border-slate-200 dark:border-slate-700"></div>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-medium ml-1">IBAN <span className="text-xs text-muted-foreground">(Externe)</span></label>
                                        <input
                                            type="text"
                                            value={newContactIban}
                                            onChange={e => {
                                                setNewContactIban(e.target.value);
                                                if (e.target.value) setNewContactEmail("");
                                            }}
                                            className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm uppercase"
                                            placeholder="FR76 ...."
                                            disabled={!!newContactEmail}
                                        />
                                    </div>

                                    {error && (
                                        <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                                            <AlertCircle className="h-4 w-4" />
                                            {error}
                                        </div>
                                    )}
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
                                        disabled={!newContactName.trim() || (!newContactEmail && !newContactIban) || isSubmitting}
                                        className="py-3 rounded-xl font-bold bg-indigo-600 text-white shadow-lg shadow-indigo-500/20 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex justify-center items-center"
                                    >
                                        {isSubmitting ? "Ajout..." : "Ajouter"}
                                    </button>
                                </div>
                            </>
                        ) : (
                            <div className="py-8 flex flex-col items-center gap-4 text-center">
                                <div className="h-16 w-16 rounded-full bg-green-100 text-green-600 flex items-center justify-center mb-2 animate-bounce">
                                    <CheckCircle2 className="h-8 w-8" />
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

            <div className="flex justify-between items-center bg-white dark:bg-slate-900 m-1 rounded-2xl shadow-sm p-1">
                {/* Search */}
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Rechercher un contact..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 rounded-xl border-none bg-transparent outline-none transition-all"
                    />
                </div>
                <button
                    onClick={() => setIsAddModalOpen(true)}
                    className="p-3 mr-1 bg-indigo-600 text-white rounded-xl shadow-lg shadow-indigo-500/20 hover:bg-indigo-700 transition-colors active:scale-95"
                >
                    <Plus className="h-5 w-5" />
                </button>
            </div>


            {/* Contacts Lists */}
            <div className="space-y-4">
                {filteredContacts.map(contact => (
                    <GlassCard key={contact.contact_id} className="flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer group">
                        <div className="flex items-center gap-4">
                            <div className={`h-12 w-12 rounded-full flex items-center justify-center font-bold text-sm ${contact.is_internal ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-300" : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"}`}>
                                {contact.initials}
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <p className="font-semibold">{contact.name}</p>
                                    {contact.is_internal && (
                                        <span className="text-[10px] bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded font-bold border border-indigo-100 dark:bg-indigo-900/20 dark:border-indigo-800">
                                            APP
                                        </span>
                                    )}
                                </div>
                                <p className="text-xs text-muted-foreground truncate max-w-[180px]">
                                    {contact.email ? contact.email : contact.iban}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <Link
                                href={`/transfer?to=${contact.email || contact.contact_id}`}
                                className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-bold rounded-lg group-hover:bg-indigo-600 group-hover:text-white transition-colors"
                            >
                                Envoyer
                            </Link>

                            <button
                                onClick={(e) => handleDelete(e, contact.contact_id)}
                                className="p-2 text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                            >
                                <Trash2 className="h-4 w-4" />
                            </button>
                        </div>
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
