"use client";

import { Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useApiKeys,
  useDeleteApiKey,
  useToggleApiKey,
} from "@/hooks/use-api-keys";
import type { ApiKey } from "@/lib/types";
import { formatDate, timeAgo } from "@/lib/utils";

export function ApiKeysTable() {
  const { data, isLoading } = useApiKeys();
  const deleteKey = useDeleteApiKey();
  const toggleKey = useToggleApiKey();

  async function handleRevoke(key: ApiKey) {
    if (!confirm(`Revoke key “${key.name}”? Clients using it will stop working.`))
      return;
    try {
      await deleteKey.mutateAsync(key.id);
      toast.success(`Key “${key.name}” revoked.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to revoke key.");
    }
  }

  async function handleToggle(key: ApiKey, enabled: boolean) {
    try {
      await toggleKey.mutateAsync({ id: key.id, enabled });
      toast.success(`Key “${key.name}” ${enabled ? "enabled" : "disabled"}.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update key.");
    }
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Key</TableHead>
          <TableHead>Enabled</TableHead>
          <TableHead>Last used</TableHead>
          <TableHead>Created</TableHead>
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
          data.map((key) => (
            <TableRow key={key.id}>
              <TableCell className="font-medium">{key.name}</TableCell>
              <TableCell className="font-mono text-xs text-muted-foreground">
                {key.preview}
              </TableCell>
              <TableCell>
                <Switch
                  checked={key.enabled}
                  disabled={toggleKey.isPending}
                  onCheckedChange={(checked) => handleToggle(key, checked)}
                  aria-label={key.enabled ? "Disable key" : "Enable key"}
                />
              </TableCell>
              <TableCell className="text-muted-foreground">
                {key.last_used_at ? timeAgo(key.last_used_at) : "Never"}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatDate(key.created_at)}
              </TableCell>
              <TableCell className="text-right">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleRevoke(key)}
                  aria-label="Revoke key"
                >
                  <Trash2 className="text-destructive" />
                </Button>
              </TableCell>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell
              colSpan={6}
              className="py-10 text-center text-muted-foreground"
            >
              No API keys yet. Create one to start authenticating requests.
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
