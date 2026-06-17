"use client";

import * as React from "react";
import { Check, Copy } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface CodeSnippetProps {
  title: string;
  description?: string;
  /** Short language/format hint shown next to the title (e.g. "JSON"). */
  language?: string;
  /** The exact text copied to the clipboard. */
  code: string;
  /** Optional banner (e.g. a roadmap caveat) rendered above the code. */
  note?: React.ReactNode;
}

export function CodeSnippet({
  title,
  description,
  language,
  code,
  note,
}: CodeSnippetProps) {
  const [copied, setCopied] = React.useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      toast.success(`${title} copied to clipboard.`);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("Couldn't access the clipboard.");
    }
  }

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
        <div className="min-w-0">
          <CardTitle className="flex items-center gap-2 text-base">
            {title}
            {language ? (
              <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                {language}
              </span>
            ) : null}
          </CardTitle>
          {description ? (
            <CardDescription className="mt-1">{description}</CardDescription>
          ) : null}
        </div>
        <Button
          size="icon"
          variant="outline"
          onClick={copy}
          aria-label={`Copy ${title}`}
          className="shrink-0"
        >
          {copied ? <Check className="text-success" /> : <Copy />}
        </Button>
      </CardHeader>
      <CardContent>
        {note ? (
          <div className="mb-3 rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs text-amber-400">
            {note}
          </div>
        ) : null}
        <pre className="overflow-x-auto rounded-md border border-border bg-muted/40 p-3 font-mono text-xs leading-relaxed">
          <code>{code}</code>
        </pre>
      </CardContent>
    </Card>
  );
}
