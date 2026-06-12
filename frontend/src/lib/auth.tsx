"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, tokenStore } from "./api";
import type { Organization, User } from "./types";

interface AuthState {
  user: User | null;
  organization: Organization | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    organization_name: string;
    name: string;
    email: string;
    password: string;
    lgpd_consent: boolean;
  }) => Promise<void>;
  logout: () => void;
  reload: () => Promise<void>;
  /** nível RBAC do usuário corrente (0 quando deslogado) */
  level: number;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    if (!tokenStore.access) {
      setUser(null);
      setOrganization(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api<{ user: User; organization: Organization }>("/auth/me");
      setUser(me.user);
      setOrganization(me.organization);
    } catch {
      tokenStore.clear();
      setUser(null);
      setOrganization(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await api<{ access_token: string; refresh_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      tokenStore.set(tokens.access_token, tokens.refresh_token);
      await reload();
    },
    [reload],
  );

  const register = useCallback(
    async (data: {
      organization_name: string;
      name: string;
      email: string;
      password: string;
      lgpd_consent: boolean;
    }) => {
      const tokens = await api<{ access_token: string; refresh_token: string }>("/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      });
      tokenStore.set(tokens.access_token, tokens.refresh_token);
      await reload();
    },
    [reload],
  );

  const logout = useCallback(() => {
    api("/auth/logout", { method: "POST" }).catch(() => undefined);
    tokenStore.clear();
    setUser(null);
    setOrganization(null);
    window.location.href = "/login";
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, organization, loading, login, register, logout, reload, level: user?.role.level ?? 0 }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
