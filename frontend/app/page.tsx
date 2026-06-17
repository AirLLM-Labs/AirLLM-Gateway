"use client";

import { Activity, Boxes, Coins, Gauge, KeyRound } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { RecentRequests } from "@/components/recent-requests";
import { StatCard } from "@/components/stat-card";
import { HealthBadge } from "@/components/status-badges";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useHealth, useStats } from "@/hooks/use-dashboard";
import { compactNumber, formatUptime } from "@/lib/utils";

export default function DashboardPage() {
  const { data: stats, isLoading } = useStats();
  const { data: health } = useHealth();

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Overview of your gateway’s models, keys, and traffic."
        action={
          <div className="flex items-center gap-3">
            {stats ? (
              <span className="hidden font-mono text-xs text-muted-foreground sm:inline">
                v{stats.version} · up {formatUptime(stats.uptime_seconds)}
              </span>
            ) : null}
            {health ? <HealthBadge status={health.status} /> : null}
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <StatCard
          label="Active models"
          value={stats?.active_models ?? 0}
          hint={`${stats?.total_models ?? 0} total registered`}
          icon={Boxes}
          loading={isLoading}
        />
        <StatCard
          label="API keys"
          value={stats?.api_keys ?? 0}
          hint="Keys authenticating /v1"
          icon={KeyRound}
          loading={isLoading}
        />
        <StatCard
          label="Total requests"
          value={(stats?.total_requests ?? 0).toLocaleString()}
          hint={`${stats?.requests_last_24h ?? 0} in last 24h`}
          icon={Activity}
          loading={isLoading}
        />
        <StatCard
          label="Tokens"
          value={compactNumber(stats?.total_tokens ?? 0)}
          hint={`${compactNumber(stats?.tokens_last_24h ?? 0)} in last 24h`}
          icon={Coins}
          loading={isLoading}
        />
        <StatCard
          label="Avg latency (24h)"
          value={`${(stats?.avg_latency_ms_24h ?? 0).toFixed(0)} ms`}
          hint={`${((stats?.error_rate_24h ?? 0) * 100).toFixed(1)}% errors`}
          icon={Gauge}
          loading={isLoading}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <RecentRequests limit={15} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Health</CardTitle>
            <CardDescription>Database and upstream servers.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Database</span>
              {health ? (
                <HealthBadge status={health.database} />
              ) : (
                <Skeleton className="h-5 w-16" />
              )}
            </div>

            <div className="border-t border-border pt-3">
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Upstreams
              </p>
              {!health ? (
                <Skeleton className="h-5 w-full" />
              ) : health.upstreams.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No upstream servers registered.
                </p>
              ) : (
                <ul className="space-y-2">
                  {health.upstreams.map((u) => (
                    <li
                      key={u.id}
                      className="flex items-center justify-between gap-2 text-sm"
                    >
                      <div className="min-w-0">
                        <p className="truncate font-medium">{u.name}</p>
                        <p className="truncate font-mono text-xs text-muted-foreground">
                          {u.endpoint_url}
                        </p>
                      </div>
                      <HealthBadge status={u.status} />
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
