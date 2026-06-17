"use client";

import { PageHeader } from "@/components/page-header";
import { SetupWizard } from "@/components/setup/setup-wizard";

export default function SetupPage() {
  return (
    <>
      <PageHeader
        title="Client Setup"
        description="Copy-paste configurations to connect your tools to the gateway — no Swagger required."
      />
      <SetupWizard />
    </>
  );
}
