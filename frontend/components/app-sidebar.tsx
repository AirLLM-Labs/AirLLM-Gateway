"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Boxes,
  KeyRound,
  LayoutDashboard,
  Plug,
  Zap,
} from "lucide-react";

import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/models", label: "Models", icon: Boxes },
  { href: "/api-keys", label: "API Keys", icon: KeyRound },
  { href: "/usage", label: "Usage", icon: BarChart3 },
  { href: "/setup", label: "Setup", icon: Plug },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-border bg-card/40">
      <div className="flex h-16 items-center gap-2 border-b border-border px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/15 text-primary">
          <Zap className="h-4 w-4" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold">AirLLM</p>
          <p className="text-xs text-muted-foreground">Gateway</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary/15 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-4 text-xs text-muted-foreground">
        <p>OpenAI-compatible</p>
        <p className="mt-1 font-mono text-[11px]">/v1 · v2</p>
      </div>
    </aside>
  );
}
