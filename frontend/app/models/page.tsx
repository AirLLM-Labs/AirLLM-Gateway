"use client";

import * as React from "react";
import { Plus } from "lucide-react";

import { ModelFormDialog } from "@/components/models/model-form-dialog";
import { ModelsTable } from "@/components/models/models-table";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function ModelsPage() {
  const [open, setOpen] = React.useState(false);

  return (
    <>
      <PageHeader
        title="Models"
        description="Register llama.cpp servers and control which are exposed via /v1."
        action={
          <Button onClick={() => setOpen(true)}>
            <Plus />
            Add model
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          <ModelsTable />
        </CardContent>
      </Card>

      {/* Create dialog (model omitted -> create mode). */}
      <ModelFormDialog open={open} onOpenChange={setOpen} model={null} />
    </>
  );
}
