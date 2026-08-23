"use client";

import { useRouter } from "next/navigation";

import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { VitalsLine } from "../../components/ui/VitalsLine";
import { clearSession } from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

// Real content (today's queue, urgency badges) is Chunk 12 per
// Frontend Design Document §3.2. Chunk 4 adds the shell/nav + design
// tokens this screen now sits inside.
export default function DoctorHome() {
  const ready = useRequireRole("doctor");
  const router = useRouter();

  if (!ready) return null;

  return (
    <AppShell
      role="doctor"
      onLogout={() => {
        clearSession();
        router.push("/login");
      }}
    >
      <VitalsLine tone="ink" />
      <Card>
        <h1>Doctor home</h1>
        <p>You&apos;re logged in as a doctor. Today&apos;s queue lands in a later chunk.</p>
      </Card>
    </AppShell>
  );
}
