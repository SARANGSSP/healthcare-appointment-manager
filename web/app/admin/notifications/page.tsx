"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../../components/shell/AppShell";
import { Badge } from "../../../components/ui/Badge";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { Table } from "../../../components/ui/Table";
import { Toast, type ToastVariant } from "../../../components/ui/Toast";
import { VitalsLine } from "../../../components/ui/VitalsLine";
import {
  clearSession,
  fetchAdminNotifications,
  retryNotification,
} from "../../../lib/api";
import { useRequireRole } from "../../../lib/useRequireRole";

export default function AdminNotificationsPage() {
  const ready = useRequireRole("admin");
  const router = useRouter();

  const [notifications, setNotifications] = useState<
    {
      id: number;
      appointment_id: number;
      type: string;
      channel: string;
      status: string;
      retry_count: number;
      last_attempt_at: string | null;
      created_at: string | null;
    }[]
  >([]);

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
      const data = await fetchAdminNotifications();
      setNotifications(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load notifications";
      showToast("failed", "Error loading notification logs", msg);
    }
  }, []);

  useEffect(() => {
    if (ready) {
      loadData();
    }
  }, [ready, loadData]);

  const handleRetryNotification = async (notifId: number) => {
    try {
      const res = await retryNotification(notifId);
      showToast("info", "Notification Retried", res.message);
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to retry notification";
      showToast("failed", "Retry failed", msg);
    }
  };

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
          <h1>System Notification Delivery Logs</h1>
          <p style={{ color: "var(--color-slate)", margin: 0 }}>
            Monitor delivery status and manually trigger retries for failed notification jobs.
          </p>
        </div>

        <VitalsLine tone="sage" />

        <Card>
          <h2>Notification Delivery Queue (Chunk 14)</h2>
          <Table
            rows={notifications}
            rowKey={(n) => n.id}
            emptyTitle="No transactional notifications logged yet."
            columns={[
              {
                key: "type",
                header: "Notification Type",
                render: (n) => <span style={{ fontWeight: 600 }}>{n.type}</span>,
              },
              {
                key: "channel",
                header: "Channel",
                render: (n) => <span style={{ textTransform: "uppercase", fontSize: "0.8125rem" }}>{n.channel}</span>,
              },
              {
                key: "status",
                header: "Status",
                render: (n) => (
                  <Badge tone={n.status === "sent" ? "sage" : n.status.includes("failed") ? "coral" : "amber"}>
                    {n.status.toUpperCase()}
                  </Badge>
                ),
              },
              {
                key: "retries",
                header: "Retries",
                render: (n) => <span style={{ fontFamily: "var(--font-mono)" }}>{n.retry_count} / 5</span>,
              },
              {
                key: "actions",
                header: "Actions",
                render: (n) => (
                  <div style={{ textAlign: "right" }}>
                    <Button size="sm" variant="ghost" onClick={() => handleRetryNotification(n.id)}>
                      Retry Job
                    </Button>
                  </div>
                ),
              },
            ]}
          />
        </Card>
      </div>
    </AppShell>
  );
}
