"use client";

import clsx from "clsx";
import {
  Banknote,
  Bot,
  Building2,
  Calculator,
  ClipboardCheck,
  FileBarChart,
  Gavel,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Package,
  Scale,
  ScrollText,
  Settings2,
  Sun,
  Users,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, minLevel: 10 },
  { href: "/empresas", label: "Empresas", icon: Building2, minLevel: 10 },
  { href: "/catalogo", label: "Produtos e Serviços", icon: Package, minLevel: 10 },
  { href: "/regras", label: "Regras Tributárias", icon: Scale, minLevel: 10 },
  { href: "/parametros", label: "Parâmetros e Premissas", icon: Settings2, minLevel: 10 },
  { href: "/simulacoes", label: "Simulações", icon: Calculator, minLevel: 10 },
  { href: "/compliance", label: "Compliance", icon: ClipboardCheck, minLevel: 10 },
  { href: "/legislacao", label: "Monitor Legislativo", icon: Gavel, minLevel: 10 },
  { href: "/relatorios", label: "Relatórios", icon: FileBarChart, minLevel: 10 },
  { href: "/assistente", label: "Assistente IA", icon: Bot, minLevel: 40 },
  { href: "/auditoria", label: "Auditoria", icon: ScrollText, minLevel: 70 },
  { href: "/usuarios", label: "Usuários", icon: Users, minLevel: 90 },
];

export function useTheme() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const stored = localStorage.getItem("tb_theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = stored ? stored === "dark" : prefersDark;
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);
  const toggle = () => {
    setDark((current) => {
      const next = !current;
      localStorage.setItem("tb_theme", next ? "dark" : "light");
      document.documentElement.classList.toggle("dark", next);
      return next;
    });
  };
  return { dark, toggle };
}

function Brand() {
  return (
    <div className="flex items-center gap-2 px-4 py-5">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
        <Banknote className="h-5 w-5" />
      </div>
      <div>
        <p className="text-sm font-bold leading-tight text-white">TaxBridge</p>
        <p className="text-[10px] uppercase tracking-widest text-slate-400">Brasil · Reforma Tributária</p>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, organization, logout, level } = useAuth();
  const { dark, toggle } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);

  const nav = NAV.filter((item) => level >= item.minLevel);

  const sidebar = (
    <div className="flex h-full flex-col bg-brand-950">
      <Brand />
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-4">
        {nav.map((item) => {
          const active = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={clsx(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors",
                active ? "bg-brand-600 text-white" : "text-slate-300 hover:bg-white/10 hover:text-white",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-white/10 p-3 text-[10px] leading-relaxed text-slate-400">
        Ferramenta de apoio à decisão. Estimativas baseadas em premissas configuráveis — não substitui
        parecer contábil/jurídico profissional.
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Sidebar desktop */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 lg:block">{sidebar}</aside>

      {/* Sidebar mobile */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/60" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64">
            {sidebar}
            <button
              className="absolute right-3 top-4 text-slate-300"
              onClick={() => setMobileOpen(false)}
              aria-label="Fechar menu"
            >
              <X className="h-5 w-5" />
            </button>
          </aside>
        </div>
      )}

      <div className="lg:pl-60">
        {/* Topbar */}
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur dark:border-slate-700 dark:bg-slate-900/90">
          <div className="flex items-center gap-3">
            <button
              className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Abrir menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">
              {organization?.name}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={toggle}
              className="rounded-md p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              aria-label="Alternar tema"
            >
              {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <div className="hidden text-right sm:block">
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">{user?.name}</p>
              <p className="text-[10px] text-slate-400">{user?.role.name}</p>
            </div>
            <button
              onClick={logout}
              className="rounded-md p-2 text-slate-500 hover:bg-slate-100 hover:text-red-600 dark:text-slate-300 dark:hover:bg-slate-800"
              aria-label="Sair"
              title="Sair"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>

        <main className="mx-auto max-w-7xl p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
