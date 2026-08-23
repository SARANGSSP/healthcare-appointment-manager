"use client";

import { useRouter } from "next/navigation";

import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { VitalsLine } from "../../components/ui/VitalsLine";
import { clearSession } from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

// Chunk 3's "done when": a patient lands here, empty, right after
// login/register. Real content ("upcoming appointment" + "Find a
// doctor") is Chunk 17 per Frontend Design Document §3.1. Chunk 4
// adds the shell/nav + design tokens this screen now sits inside.
export default function PatientHome() {
  const ready = useRequireRole("patient");
  const router = useRouter();

  if (!ready) return null;

  return (
    <AppShell
      role="patient"
      narrow
      onLogout={() => {
        clearSession();
        router.push("/login");
      }}
    >
      <VitalsLine tone="sage" />
      <Card>
        <h1>Patient home</h1>
        <p>You&apos;re logged in as a patient. Search and booking land in later chunks.</p>
      </Card>
    </AppShell>
  );
}
