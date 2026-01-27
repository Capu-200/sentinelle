import { logoutAction } from "@/app/actions/auth";
import { ArrowLeft, User, Shield, Key } from "lucide-react";
import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { GlassCard } from "@/components/ui/glass-card";

async function getUserProfile() {
  const cookieStore = await cookies();
  const token = cookieStore.get("auth-token");

  if (!token) {
    redirect("/login");
  }

  try {
    const res = await fetch("http://127.0.0.1:8000/dashboard/", {
      headers: {
        "Authorization": `Bearer ${token.value}`,
      },
      cache: "no-store",
    });

    if (!res.ok) {
      return null;
    }

    return await res.json();
  } catch (error) {
    return null; // Handle error appropriately
  }
}


export default async function ProfilePage() {
  const data = await getUserProfile();

  if (!data) {
    redirect("/login");
  }

  const { user } = data;

  return (
    <div className="max-w-md mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/" className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
          <ArrowLeft className="h-6 w-6" />
        </Link>
        <h1 className="text-2xl font-bold">Mon Profil</h1>
      </div>

      <GlassCard className="p-8 space-y-6">
        <div className="flex flex-col items-center">
          <div className="h-24 w-24 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4 ring-4 ring-white dark:ring-slate-900 shadow-xl">
            <User className="h-12 w-12 text-slate-400" />
          </div>
          <h2 className="text-xl font-bold">{user.full_name}</h2>
          <p className="text-sm text-muted-foreground">{user.email}</p>
        </div>

        <div className="space-y-4 pt-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium text-sm">Niveau de risque</p>
                <p className="text-xs text-muted-foreground">Analysé par IA</p>
              </div>
            </div>
            <span className="font-bold text-sm px-2 py-1 rounded-md bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
              {user.risk_level}
            </span>
          </div>

          <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
                <Key className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium text-sm">ID Utilisateur</p>
                <p className="text-xs text-muted-foreground font-mono truncate max-w-[150px]">{user.user_id}</p>
              </div>
            </div>
          </div>
        </div>

        <form action={logoutAction} className="pt-6">
          <button className="w-full py-3 rounded-xl bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/20 dark:hover:bg-red-900/30 dark:text-red-400 font-medium transition-colors">
            Se déconnecter
          </button>
        </form>
      </GlassCard>
    </div>
  );
}
