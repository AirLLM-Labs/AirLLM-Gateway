"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useLogs } from "@/hooks/use-dashboard";
import { timeAgo } from "@/lib/utils";

import { StatusCodeBadge } from "./status-badges";

export function RecentRequests({ limit = 15 }: { limit?: number }) {
  const { data, isLoading } = useLogs(limit);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent requests</CardTitle>
        <CardDescription>Latest traffic through the gateway.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Endpoint</TableHead>
              <TableHead>Model</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Latency</TableHead>
              <TableHead className="text-right">When</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 5 }).map((__, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : data && data.length > 0 ? (
              data.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="font-mono text-xs">{log.endpoint}</TableCell>
                  <TableCell>{log.model_used ?? "—"}</TableCell>
                  <TableCell>
                    <StatusCodeBadge code={log.status_code} />
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {log.latency_ms.toFixed(0)} ms
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    {timeAgo(log.created_at)}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="py-10 text-center text-muted-foreground"
                >
                  No requests yet. Point an OpenAI client at the gateway to see
                  traffic here.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
