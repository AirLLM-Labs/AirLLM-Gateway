"use client";

import * as React from "react";
import { Pencil, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useHealth } from "@/hooks/use-dashboard";
import { useDeleteModel, useModels } from "@/hooks/use-models";
import type { Model, UpstreamHealth } from "@/lib/types";
import { cn } from "@/lib/utils";

import { EnabledBadge } from "../status-badges";
import { ModelFormDialog } from "./model-form-dialog";

function ModelHealthCell({ health }: { health?: UpstreamHealth }) {
  if (!health) {
    return <span className="text-xs text-muted-foreground">—</span>;
  }
  const ok = health.status === "ok";
  return (
    <span className="flex items-center gap-2 text-xs">
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          ok ? "bg-success" : "bg-destructive",
        )}
      />
      <span className={ok ? "text-foreground" : "text-destructive"}>
        {ok ? "Healthy" : "Down"}
      </span>
      {health.latency_ms != null ? (
        <span className="font-mono text-muted-foreground">
          {health.latency_ms.toFixed(0)} ms
        </span>
      ) : null}
    </span>
  );
}

export function ModelsTable() {
  const { data, isLoading } = useModels();
  const { data: health } = useHealth();
  const deleteModel = useDeleteModel();
  const [editing, setEditing] = React.useState<Model | null>(null);
  const [open, setOpen] = React.useState(false);

  const healthById = React.useMemo(() => {
    const map = new Map<number, UpstreamHealth>();
    health?.upstreams.forEach((u) => map.set(u.id, u));
    return map;
  }, [health]);

  async function handleDelete(model: Model) {
    if (!confirm(`Delete model “${model.name}”? This cannot be undone.`)) return;
    try {
      await deleteModel.mutateAsync(model.id);
      toast.success(`Model “${model.name}” deleted.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete model.");
    }
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Model id</TableHead>
            <TableHead>Endpoint</TableHead>
            <TableHead>Capabilities</TableHead>
            <TableHead>Health</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <TableRow key={i}>
                {Array.from({ length: 6 }).map((__, j) => (
                  <TableCell key={j}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : data && data.length > 0 ? (
            data.map((model) => (
              <TableRow key={model.id}>
                <TableCell className="font-medium">{model.name}</TableCell>
                <TableCell className="font-mono text-xs text-muted-foreground">
                  {model.endpoint_url}
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {model.capabilities.map((c) => (
                      <Badge key={c} variant="outline">
                        {c}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell>
                  <ModelHealthCell health={healthById.get(model.id)} />
                </TableCell>
                <TableCell>
                  <EnabledBadge enabled={model.enabled} />
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        setEditing(model);
                        setOpen(true);
                      }}
                      aria-label="Edit model"
                    >
                      <Pencil />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(model)}
                      aria-label="Delete model"
                    >
                      <Trash2 className="text-destructive" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell
                colSpan={6}
                className="py-10 text-center text-muted-foreground"
              >
                No models registered yet. Add your first llama.cpp server above.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      <ModelFormDialog open={open} onOpenChange={setOpen} model={editing} />
    </>
  );
}
