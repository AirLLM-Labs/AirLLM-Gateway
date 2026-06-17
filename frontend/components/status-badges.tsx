import { Badge } from "@/components/ui/badge";
import type { HealthStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const HEALTH_VARIANT: Record<HealthStatus, "success" | "warning" | "destructive"> = {
  ok: "success",
  degraded: "warning",
  down: "destructive",
};

const HEALTH_LABEL: Record<HealthStatus, string> = {
  ok: "Healthy",
  degraded: "Degraded",
  down: "Down",
};

export function HealthBadge({ status }: { status: HealthStatus }) {
  return (
    <Badge variant={HEALTH_VARIANT[status]} className="gap-1.5">
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          status === "ok" && "bg-success",
          status === "degraded" && "bg-amber-400",
          status === "down" && "bg-destructive",
        )}
      />
      {HEALTH_LABEL[status]}
    </Badge>
  );
}

export function StatusCodeBadge({ code }: { code: number }) {
  const variant =
    code < 300
      ? "success"
      : code < 400
        ? "secondary"
        : code < 500
          ? "warning"
          : "destructive";
  return <Badge variant={variant}>{code}</Badge>;
}

export function EnabledBadge({ enabled }: { enabled: boolean }) {
  return (
    <Badge variant={enabled ? "success" : "secondary"}>
      {enabled ? "Enabled" : "Disabled"}
    </Badge>
  );
}
