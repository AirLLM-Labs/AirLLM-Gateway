/**
 * Typed client for the dashboard.
 *
 * All calls go through the same-origin BFF proxy at /api/proxy/*, which injects
 * the admin token server-side. The browser therefore never holds the token.
 */
import type {
  ApiKey,
  ApiKeyCreated,
  DashboardStats,
  HealthResponse,
  Model,
  ModelInput,
  RequestLog,
  UsageResponse,
} from "./types";

const PROXY_BASE = "/api/proxy";

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${PROXY_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail ?? body.error?.message ?? body.error ?? detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  // --- Dashboard / health ---
  getStats: () => request<DashboardStats>("/admin/stats"),
  getHealth: () => request<HealthResponse>("/health"),
  getLogs: (limit = 50) => request<RequestLog[]>(`/admin/logs?limit=${limit}`),
  getUsage: (days = 7) => request<UsageResponse>(`/admin/usage?days=${days}`),

  // --- Models ---
  listModels: () => request<Model[]>("/admin/models"),
  createModel: (data: ModelInput) =>
    request<Model>("/admin/models", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateModel: (id: number, data: Partial<ModelInput>) =>
    request<Model>(`/admin/models/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteModel: (id: number) =>
    request<void>(`/admin/models/${id}`, { method: "DELETE" }),

  // --- API keys ---
  listApiKeys: () => request<ApiKey[]>("/admin/api-keys"),
  createApiKey: (name: string) =>
    request<ApiKeyCreated>("/admin/api-keys", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),
  updateApiKey: (id: number, data: { enabled?: boolean; name?: string }) =>
    request<ApiKey>(`/admin/api-keys/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteApiKey: (id: number) =>
    request<void>(`/admin/api-keys/${id}`, { method: "DELETE" }),
};
