"use client";

import { ApiKeysTable } from "@/components/api-keys/api-keys-table";
import { CreateKeyDialog } from "@/components/api-keys/create-key-dialog";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";

export default function ApiKeysPage() {
  return (
    <>
      <PageHeader
        title="API Keys"
        description="Keys authenticate clients against the OpenAI-compatible /v1 endpoints."
        action={<CreateKeyDialog />}
      />

      <Card>
        <CardContent className="p-0">
          <ApiKeysTable />
        </CardContent>
      </Card>
    </>
  );
}
