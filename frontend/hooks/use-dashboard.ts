"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useUiStore } from "@/store/ui-store";

export function useStats() {
  const refetchInterval = useUiStore((s) => s.refreshInterval);
  return useQuery({ queryKey: ["stats"], queryFn: api.getStats, refetchInterval });
}

export function useHealth() {
  const refetchInterval = useUiStore((s) => s.refreshInterval);
  return useQuery({ queryKey: ["health"], queryFn: api.getHealth, refetchInterval });
}

export function useLogs(limit = 25) {
  const refetchInterval = useUiStore((s) => s.refreshInterval);
  return useQuery({
    queryKey: ["logs", limit],
    queryFn: () => api.getLogs(limit),
    refetchInterval,
  });
}
