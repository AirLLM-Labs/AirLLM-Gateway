"use client";

import { PageHeader } from "@/components/page-header";
import { UsageView } from "@/components/usage/usage-view";
import { useUsage } from "@/hooks/use-usage";

export default function UsagePage() {
  const { data, isLoading } = useUsage(7);

  return (
    <>
      <PageHeader
        title="Usage"
        description="Requests, tokens, and latency across your models over the last 7 days."
      />
      <UsageView data={data} isLoading={isLoading} />
    </>
  );
}
