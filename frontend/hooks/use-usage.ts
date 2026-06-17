"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function useUsage(days = 7) {
  return useQuery({
    queryKey: ["usage", days],
    queryFn: () => api.getUsage(days),
  });
}
