"use client";

import { useRouter } from "next/navigation";

import { AppShell } from "../../../components/shell/AppShell";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { VitalsLine } from "../../../components/ui/VitalsLine";
import { clearSession } from "../../../lib/api";
import { useRequireRole } from "../../../lib/useRequireRole";

export default function PatientAccountPage() {
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
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        <div>
          <h1>Patient Account & Preferences</h1>
          <p style={{ color: "var(--color-slate)", margin: 0 }}>
            Manage notification preferences and account settings.
          </p>
        </div>

        <VitalsLine tone="sage" animate />

        <Card>
          <h2>Account Details</h2>
          <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <p style={{ margin: 0 }}>
              <strong>Role:</strong> Patient
            </p>
            <p style={{ margin: 0 }}>
              <strong>Notifications:</strong> Email (Active)
            </p>
            <p style={{ margin: 0 }}>
              <strong>Google Calendar Sync:</strong> Enabled
            </p>
          </div>

          <div style={{ marginTop: "1.5rem" }}>
            <Button
              variant="ghost"
              onClick={() => {
                clearSession();
                router.push("/login");
              }}
            >
              Sign Out of Account
            </Button>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
