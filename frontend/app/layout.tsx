import type { Metadata } from "next";

import { AppSidebar } from "@/components/app-sidebar";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "AirLLM Gateway",
  description: "Self-hosted, OpenAI-compatible gateway for local llama.cpp models.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>
        <Providers>
          <div className="flex">
            <AppSidebar />
            <main className="h-screen flex-1 overflow-y-auto">
              <div className="mx-auto max-w-6xl px-8 py-8">{children}</div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
