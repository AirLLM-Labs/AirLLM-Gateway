"use client";

import * as React from "react";
import { Check, Copy, Plus, TriangleAlert } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateApiKey } from "@/hooks/use-api-keys";

export function CreateKeyDialog() {
  const createKey = useCreateApiKey();
  const [open, setOpen] = React.useState(false);
  const [name, setName] = React.useState("");
  const [createdKey, setCreatedKey] = React.useState<string | null>(null);
  const [copied, setCopied] = React.useState(false);

  function reset() {
    setName("");
    setCreatedKey(null);
    setCopied(false);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const result = await createKey.mutateAsync(name.trim() || "Untitled key");
      setCreatedKey(result.key);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create key.");
    }
  }

  async function copyKey() {
    if (!createdKey) return;
    await navigator.clipboard.writeText(createdKey);
    setCopied(true);
    toast.success("API key copied to clipboard.");
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus />
          Create key
        </Button>
      </DialogTrigger>
      <DialogContent>
        {createdKey ? (
          <>
            <DialogHeader>
              <DialogTitle>API key created</DialogTitle>
              <DialogDescription>
                Copy it now — for security it will never be shown again.
              </DialogDescription>
            </DialogHeader>
            <div className="flex items-center gap-2 rounded-md border border-border bg-muted/40 p-3">
              <code className="flex-1 break-all font-mono text-sm">{createdKey}</code>
              <Button size="icon" variant="outline" onClick={copyKey}>
                {copied ? <Check className="text-success" /> : <Copy />}
              </Button>
            </div>
            <div className="flex items-start gap-2 text-xs text-amber-400">
              <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>
                Store this key in your client&apos;s <code>api_key</code> field.
              </span>
            </div>
            <DialogFooter>
              <Button onClick={() => setOpen(false)}>Done</Button>
            </DialogFooter>
          </>
        ) : (
          <form onSubmit={handleCreate}>
            <DialogHeader>
              <DialogTitle>Create API key</DialogTitle>
              <DialogDescription>
                Give the key a name so you can recognise it later.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-2 py-4">
              <Label htmlFor="key-name">Name</Label>
              <Input
                id="key-name"
                placeholder="Production app"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createKey.isPending}>
                {createKey.isPending ? "Creating…" : "Create key"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
