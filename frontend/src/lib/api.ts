const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const BASE = `${API_URL}/api/v1`;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const tokenStore = {
  get access() {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("tb_access");
  },
  get refresh() {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("tb_refresh");
  },
  set(access: string, refresh: string) {
    localStorage.setItem("tb_access", access);
    localStorage.setItem("tb_refresh", refresh);
  },
  clear() {
    localStorage.removeItem("tb_access");
    localStorage.removeItem("tb_refresh");
  },
};

async function tryRefresh(): Promise<boolean> {
  const refresh = tokenStore.refresh;
  if (!refresh) return false;
  const res = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) {
    tokenStore.clear();
    return false;
  }
  const data = await res.json();
  tokenStore.set(data.access_token, data.refresh_token);
  return true;
}

function extractDetail(body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) {
      const first = detail[0];
      const field = Array.isArray(first.loc) ? first.loc.slice(1).join(".") : "";
      return field ? `${field}: ${first.msg}` : first.msg;
    }
  }
  return "Erro inesperado. Tente novamente.";
}

async function rawRequest(path: string, options: RequestInit = {}, retry = true): Promise<Response> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = tokenStore.access;
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 401 && retry && tokenStore.refresh) {
    const refreshed = await tryRefresh();
    if (refreshed) return rawRequest(path, options, false);
    if (typeof window !== "undefined") window.location.href = "/login";
  }
  return res;
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await rawRequest(path, options);
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, extractDetail(body));
  return body as T;
}

export async function apiDownload(path: string, filename: string): Promise<void> {
  const res = await rawRequest(path);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, extractDetail(body));
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export const apiUrl = API_URL;
