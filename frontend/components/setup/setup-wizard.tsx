"use client";

import * as React from "react";
import { KeyRound, Plus } from "lucide-react";
import { toast } from "sonner";

import { CodeSnippet } from "@/components/setup/code-snippet";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateApiKey } from "@/hooks/use-api-keys";
import { useModels } from "@/hooks/use-models";

const KEY_PLACEHOLDER = "sk-airllm_xxxxxxxxxxxxxxxx";
const DEFAULT_BASE_URL = "http://localhost:4000/v1";

export function SetupWizard() {
  const createKey = useCreateApiKey();
  const { data: models } = useModels();

  const [baseUrl, setBaseUrl] = React.useState(DEFAULT_BASE_URL);
  const [apiKey, setApiKey] = React.useState("");
  const [justCreated, setJustCreated] = React.useState(false);

  // The dashboard and the API run on different ports today (3000 vs 4000), so
  // keep the current host but default to the gateway port. Set after mount to
  // avoid an SSR/hydration mismatch; the field stays user-editable.
  React.useEffect(() => {
    const host = window.location.hostname || "localhost";
    setBaseUrl(`http://${host}:4000/v1`);
  }, []);

  const model = models?.find((m) => m.enabled)?.name ?? models?.[0]?.name ?? "coder";
  const key = apiKey.trim() || KEY_PLACEHOLDER;

  async function handleCreateKey() {
    try {
      const created = await createKey.mutateAsync("Setup wizard");
      setApiKey(created.key);
      setJustCreated(true);
      toast.success("API key created — it's filled in below (shown once).");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create key.");
    }
  }

  const snippets = buildSnippets(baseUrl, key, model);

  return (
    <div className="space-y-6">
      {/* Step 1 — connection details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">1. Connection details</CardTitle>
          <CardDescription>
            These values fill every snippet below. Create a key here or paste one
            you already saved — keys are only shown once.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="grid gap-2">
            <Label htmlFor="base-url">API base URL</Label>
            <Input
              id="base-url"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              className="font-mono text-sm"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="api-key">API key</Label>
            <div className="flex gap-2">
              <Input
                id="api-key"
                value={apiKey}
                placeholder={KEY_PLACEHOLDER}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  setJustCreated(false);
                }}
                className="font-mono text-sm"
              />
              <Button
                type="button"
                variant="outline"
                onClick={handleCreateKey}
                disabled={createKey.isPending}
                className="shrink-0"
              >
                {createKey.isPending ? (
                  "Creating…"
                ) : (
                  <>
                    <Plus />
                    New key
                  </>
                )}
              </Button>
            </div>
            {justCreated ? (
              <p className="flex items-center gap-1.5 text-xs text-amber-400">
                <KeyRound className="h-3.5 w-3.5" />
                Copy this key into your client now — it won&apos;t be shown again.
              </p>
            ) : (
              <p className="text-xs text-muted-foreground">
                Model used in examples: <code>{model}</code>
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Step 2 — client snippets */}
      <div>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-muted-foreground">
          2. Configure your client
        </h2>
        <div className="grid gap-4 lg:grid-cols-2">
          {snippets.map((s) => (
            <CodeSnippet key={s.title} {...s} />
          ))}
        </div>
      </div>
    </div>
  );
}

interface Snippet {
  title: string;
  description?: string;
  language?: string;
  code: string;
  note?: React.ReactNode;
}

function buildSnippets(baseUrl: string, key: string, model: string): Snippet[] {
  return [
    {
      title: "VS Code",
      description: "Add to your settings.json (OpenAI-compatible extensions).",
      language: "json",
      code: `{
  "openai.base_url": "${baseUrl}",
  "openai.api_key": "${key}"
}`,
    },
    {
      title: "Continue.dev",
      description: "Add a model block to ~/.continue/config.json.",
      language: "json",
      code: `{
  "models": [
    {
      "title": "AirLLM (${model})",
      "provider": "openai",
      "model": "${model}",
      "apiBase": "${baseUrl}",
      "apiKey": "${key}"
    }
  ]
}`,
    },
    {
      title: "OpenAI SDK — Python",
      description: "Point the official OpenAI client at the gateway.",
      language: "python",
      code: `from openai import OpenAI

client = OpenAI(
    base_url="${baseUrl}",
    api_key="${key}",
)

resp = client.chat.completions.create(
    model="${model}",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(resp.choices[0].message.content)`,
    },
    {
      title: "OpenAI SDK — Node",
      description: "Works with the openai npm package.",
      language: "ts",
      code: `import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "${baseUrl}",
  apiKey: "${key}",
});

const res = await client.chat.completions.create({
  model: "${model}",
  messages: [{ role: "user", content: "Hello!" }],
});
console.log(res.choices[0].message.content);`,
    },
    {
      title: "curl",
      description: "Quick smoke test from a terminal.",
      language: "bash",
      code: `curl ${baseUrl}/chat/completions \\
  -H "Authorization: Bearer ${key}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "${model}",
    "messages": [{"role": "user", "content": "hi"}]
  }'`,
    },
    {
      title: "Claude Code",
      description: "Set these environment variables before launching.",
      language: "bash",
      note: (
        <>
          AirLLM is <strong>OpenAI-compatible</strong>; Claude Code expects
          Anthropic-style endpoints. Anthropic compatibility is on the roadmap —
          until then, use the OpenAI SDK snippets above.
        </>
      ),
      code: `export ANTHROPIC_BASE_URL="${baseUrl.replace(/\/v1$/, "")}"
export ANTHROPIC_API_KEY="${key}"`,
    },
  ];
}
