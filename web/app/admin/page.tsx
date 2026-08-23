"use client";

import { useRouter } from "next/navigation";

import { AppShell } from "../../components/shell/AppShell";
import { Card } from "../../components/ui/Card";
import { VitalsLine } from "../../components/ui/VitalsLine";
import { clearSession } from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

// Real content (doctors table, notifications, overview) is Chunk 5
// onward per Frontend Design Document §3.3. Chunk 4 adds the
// shell/nav + design tokens this screen now sits inside.
export default function AdminHome() {
  const ready = useRequireRole("admin");
  const router = useRouter();

  if (!ready) return null;

  return (
    <AppShell
      role="admin"
      onLogout={() => {
        clearSession();
        router.push("/login");
      }}
    >
      <VitalsLine tone="ink" />
      <Card>
        <h1>Admin home</h1>
        <p>You&apos;re logged in as an admin. Doctor management lands in a later chunk.</p>
      </Card>
    </AppShell>
  );
}
