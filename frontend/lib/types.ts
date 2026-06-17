/** Shared types mirroring the backend API schemas. */

export type Capability = "chat" | "vision" | string;

export interface Model {
  id: number;
  name: string;
  provider: string;
  endpoint_url: string;
  enabled: boolean;
  capabilities: Capability[];
  created_at: string;
}

export interface ModelInput {
  name: string;
  provider?: string;
  endpoint_url: string;
  enabled?: boolean;
  capabilities?: Capability[];
}

export interface ApiKey {
  id: number;
  name: string;
  preview: string;
  enabled: boolean;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiKeyCreated extends ApiKey {
  /** Plaintext key, returned only once at creation. */
  key: string;
}

export interface RequestLog {
  id: number;
  endpoint: string;
  model_used: string | null;
  latency_ms: number;
  status_code: number;
  created_at: string;
}

export interface DashboardStats {
  active_models: number;
  total_models: number;
  api_keys: number;
  total_requests: number;
  requests_last_24h: number;
  error_rate_24h: number;
  avg_latency_ms_24h: number;
  total_tokens: number;
  tokens_last_24h: number;
  version: string;
  uptime_seconds: number;
  health: HealthStatus;
}

export interface UsageDaily {
  day: string;
  requests: number;
  tokens: number;
}

export interface UsagePerModel {
  model: string;
  requests: number;
  tokens: number;
  avg_latency_ms: number;
}

export interface UsageResponse {
  days: number;
  requests_this_week: number;
  tokens_this_week: number;
  daily: UsageDaily[];
  per_model: UsagePerModel[];
}

export type HealthStatus = "ok" | "degraded" | "down";

export interface UpstreamHealth {
  id: number;
  name: string;
  endpoint_url: string;
  status: HealthStatus;
  latency_ms: number | null;
  detail: string | null;
}

export interface HealthResponse {
  status: HealthStatus;
  database: HealthStatus;
  upstreams: UpstreamHealth[];
}
