"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { StatCard } from "@/components/stat-card";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { UsageResponse } from "@/lib/types";
import { compactNumber } from "@/lib/utils";
import { Activity, Coins, Gauge } from "lucide-react";

const REQUEST_COLOR = "hsl(152, 65%, 45%)";
const TOKEN_COLOR = "hsl(190, 70%, 50%)";
const AXIS_COLOR = "hsl(240, 5%, 60%)";
const GRID_COLOR = "hsl(240, 5%, 16%)";

const TOOLTIP_STYLE = {
  backgroundColor: "hsl(240, 8%, 7%)",
  border: "1px solid hsl(240, 5%, 16%)",
  borderRadius: 8,
  fontSize: 12,
} as const;

function shortDay(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function UsageView({
  data,
  isLoading,
}: {
  data?: UsageResponse;
  isLoading: boolean;
}) {
  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <Skeleton className="h-72" />
        <Skeleton className="h-72" />
      </div>
    );
  }

  const daily = data.daily.map((d) => ({ ...d, label: shortDay(d.day) }));
  const avgLatency =
    data.per_model.length > 0
      ? data.per_model.reduce((s, m) => s + m.avg_latency_ms, 0) /
        data.per_model.length
      : 0;
  const maxModelRequests = Math.max(1, ...data.per_model.map((m) => m.requests));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label={`Requests (${data.days}d)`}
          value={data.requests_this_week.toLocaleString()}
          icon={Activity}
        />
        <StatCard
          label={`Tokens (${data.days}d)`}
          value={compactNumber(data.tokens_this_week)}
          icon={Coins}
        />
        <StatCard
          label="Avg latency / model"
          value={`${avgLatency.toFixed(0)} ms`}
          icon={Gauge}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Requests per day</CardTitle>
          <CardDescription>Traffic over the last {data.days} days.</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={daily} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} vertical={false} />
              <XAxis dataKey="label" stroke={AXIS_COLOR} fontSize={12} tickLine={false} />
              <YAxis stroke={AXIS_COLOR} fontSize={12} allowDecimals={false} tickLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "hsl(240, 5%, 14%)" }} />
              <Bar dataKey="requests" fill={REQUEST_COLOR} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Tokens per day</CardTitle>
          <CardDescription>Total tokens processed per day.</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={daily} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="tokenFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={TOKEN_COLOR} stopOpacity={0.4} />
                  <stop offset="95%" stopColor={TOKEN_COLOR} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} vertical={false} />
              <XAxis dataKey="label" stroke={AXIS_COLOR} fontSize={12} tickLine={false} />
              <YAxis
                stroke={AXIS_COLOR}
                fontSize={12}
                tickLine={false}
                tickFormatter={(v) => compactNumber(Number(v))}
              />
              <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ stroke: GRID_COLOR }} />
              <Area
                type="monotone"
                dataKey="tokens"
                stroke={TOKEN_COLOR}
                strokeWidth={2}
                fill="url(#tokenFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Requests per model</CardTitle>
          <CardDescription>Which models are getting the traffic.</CardDescription>
        </CardHeader>
        <CardContent>
          {data.per_model.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No traffic in this window yet.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(120, data.per_model.length * 48)}>
              <BarChart
                layout="vertical"
                data={data.per_model}
                margin={{ top: 0, right: 16, left: 8, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} horizontal={false} />
                <XAxis type="number" stroke={AXIS_COLOR} fontSize={12} allowDecimals={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="model"
                  stroke={AXIS_COLOR}
                  fontSize={12}
                  width={90}
                  tickLine={false}
                />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "hsl(240, 5%, 14%)" }} />
                <Bar dataKey="requests" radius={[0, 4, 4, 0]}>
                  {data.per_model.map((m) => (
                    <Cell
                      key={m.model}
                      fillOpacity={0.35 + 0.65 * (m.requests / maxModelRequests)}
                      fill={REQUEST_COLOR}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
