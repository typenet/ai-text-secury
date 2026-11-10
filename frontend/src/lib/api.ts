export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type RiskBand = "safe" | "attention" | "high" | "critical";

export interface Finding {
  rule: string;
  severity: Severity;
  technique: string;
  page: number | null;
  bbox: [number, number, number, number] | null;
  text: string;
  confidence: number;
  detector_version: string;
  evidence: Record<string, unknown>;
}

export interface Scan {
  id: string;
  status: "queued" | "running" | "done" | "failed";
  score: number | null;
  band: RiskBand | null;
  engine_version: string | null;
  error: string | null;
  created_at: string;
  finished_at: string | null;
  document: { id: string; filename: string; doc_type: string; size_bytes: number; page_count: number | null };
  findings: Finding[];
}

// MVP: a API key fica no navegador do usuário. Trocar por login/sessão antes de produção.
const KEY_STORAGE = "ats_api_key";

export function getApiKey(): string {
  try {
    return localStorage.getItem(KEY_STORAGE) ?? "";
  } catch {
    return "";
  }
}

export function setApiKey(key: string) {
  try {
    localStorage.setItem(KEY_STORAGE, key);
  } catch {
    /* modo privado: segue sem persistir */
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "X-API-Key": getApiKey(), ...(init.headers ?? {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Erro ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function createScan(file: File): Promise<Scan> {
  const form = new FormData();
  form.append("file", file);
  return request<Scan>("/v1/scans", { method: "POST", body: form });
}

export function getScan(id: string): Promise<Scan> {
  return request<Scan>(`/v1/scans/${id}`);
}
