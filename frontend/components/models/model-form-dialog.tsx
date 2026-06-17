"use client";

import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useCreateModel, useUpdateModel } from "@/hooks/use-models";
import type { Model } from "@/lib/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** When provided, the dialog edits this model; otherwise it creates one. */
  model?: Model | null;
}

export function ModelFormDialog({ open, onOpenChange, model }: Props) {
  const isEdit = Boolean(model);
  const createModel = useCreateModel();
  const updateModel = useUpdateModel();

  const [name, setName] = React.useState("");
  const [endpoint, setEndpoint] = React.useState("");
  const [capabilities, setCapabilities] = React.useState("chat");
  const [enabled, setEnabled] = React.useState(true);

  // Sync form state whenever the dialog opens for a new target.
  React.useEffect(() => {
    if (open) {
      setName(model?.name ?? "");
      setEndpoint(model?.endpoint_url ?? "");
      setCapabilities((model?.capabilities ?? ["chat"]).join(", "));
      setEnabled(model?.enabled ?? true);
    }
  }, [open, model]);

  const pending = createModel.isPending || updateModel.isPending;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const caps = capabilities
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);

    const payload = {
      name: name.trim(),
      endpoint_url: endpoint.trim(),
      capabilities: caps.length ? caps : ["chat"],
      enabled,
    };

    try {
      if (isEdit && model) {
        await updateModel.mutateAsync({ id: model.id, data: payload });
        toast.success(`Model “${payload.name}” updated.`);
      } else {
        await createModel.mutateAsync(payload);
        toast.success(`Model “${payload.name}” added.`);
      }
      onOpenChange(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEdit ? "Edit model" : "Add model"}</DialogTitle>
            <DialogDescription>
              Map a public model id to an upstream llama.cpp server.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Model id</Label>
              <Input
                id="name"
                placeholder="qwen2.5-coder"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="endpoint">Endpoint URL</Label>
              <Input
                id="endpoint"
                placeholder="http://127.0.0.1:8080"
                value={endpoint}
                onChange={(e) => setEndpoint(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="caps">Capabilities</Label>
              <Input
                id="caps"
                placeholder="chat, vision"
                value={capabilities}
                onChange={(e) => setCapabilities(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Comma-separated tags, e.g. <code>chat</code> or <code>vision</code>.
              </p>
            </div>
            <div className="flex items-center justify-between rounded-md border border-border p-3">
              <div>
                <Label htmlFor="enabled">Enabled</Label>
                <p className="text-xs text-muted-foreground">
                  Disabled models are hidden from <code>/v1</code> clients.
                </p>
              </div>
              <Switch id="enabled" checked={enabled} onCheckedChange={setEnabled} />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={pending}>
              {pending ? "Saving…" : isEdit ? "Save changes" : "Add model"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
