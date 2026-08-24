"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../../components/shell/AppShell";
import { Card } from "../../../components/ui/Card";
import { Toast, type ToastVariant } from "../../../components/ui/Toast";
import { VitalsLine } from "../../../components/ui/VitalsLine";
import {
  clearSession,
  fetchAdminOverview,
} from "../../../lib/api";
import { useRequireRole } from "../../../lib/useRequireRole";

export default function AdminOverviewPage() {
  const ready = useRequireRole("admin");
  const router = useRouter();

  const [overview, setOverview] = useState<{
    total_bookings: number;
    active_doctors: number;
    total_patients: number;
    failed_notifications: number;
    system_status: string;
  } | null>(null);

  const [toast, setToast] = useState<{
    variant: ToastVariant;
    title: string;
    body?: string;
  } | null>(null);

  const showToast = (variant: ToastVariant, title: string, body?: string) => {
    setToast({ variant, title, body });
    setTimeout(() => setToast(null), 5000);
  };

  const loadData = useCallback(async () => {
    try {
      const data = await fetchAdminOverview();
      setOverview(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load admin overview";
      showToast("failed", "Error loading metrics", msg);
    }
  }, []);

  useEffect(() => {
    if (ready) {
      loadData();
    }
  }, [ready, loadData]);

  if (!ready) return null;

  return (
    <AppShell
      role="admin"
      onLogout={() => {
        clearSession();
        router.push("/login");
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        {toast && <Toast variant={toast.variant} title={toast.title}>{toast.body}</Toast>}

        <div>
          <h1>Admin Overview Dashboard</h1>
          <p style={{ color: "var(--color-slate)", margin: 0 }}>
            Live platform metrics, booking volume, and health status.
          </p>
        </div>

        <VitalsLine tone="sage" animate />

        {overview && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
            <Card style={{ padding: "1rem" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--color-slate)", textTransform: "uppercase" }}>Total Bookings</span>
              <strong style={{ fontSize: "1.75rem", display: "block", fontFamily: "var(--font-mono)", marginTop: "0.25rem" }}>
                {overview.total_bookings}
              </strong>
            </Card>

            <Card style={{ padding: "1rem" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--color-slate)", textTransform: "uppercase" }}>Active Doctors</span>
              <strong style={{ fontSize: "1.75rem", display: "block", fontFamily: "var(--font-mono)", marginTop: "0.25rem" }}>
                {overview.active_doctors}
              </strong>
            </Card>

            <Card style={{ padding: "1rem" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--color-slate)", textTransform: "uppercase" }}>Total Patients</span>
              <strong style={{ fontSize: "1.75rem", display: "block", fontFamily: "var(--font-mono)", marginTop: "0.25rem" }}>
                {overview.total_patients}
              </strong>
            </Card>

            <Card style={{ padding: "1rem" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--color-slate)", textTransform: "uppercase" }}>Failed Notifications</span>
              <strong style={{ fontSize: "1.75rem", display: "block", fontFamily: "var(--font-mono)", color: overview.failed_notifications > 0 ? "var(--color-coral)" : "var(--color-sage)", marginTop: "0.25rem" }}>
                {overview.failed_notifications}
              </strong>
            </Card>
          </div>
        )}
      </div>
    </AppShell>
  );
}
