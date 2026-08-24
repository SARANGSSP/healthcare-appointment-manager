"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../../components/shell/AppShell";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { Input } from "../../../components/ui/Input";
import { Table } from "../../../components/ui/Table";
import { Toast, type ToastVariant } from "../../../components/ui/Toast";
import { VitalsLine } from "../../../components/ui/VitalsLine";
import {
  clearSession,
  deleteDoctorLeave,
  fetchDoctorLeave,
  fetchDoctorMe,
  markDoctorLeave,
  type Doctor,
  type DoctorLeave,
} from "../../../lib/api";
import { useRequireRole } from "../../../lib/useRequireRole";

export default function DoctorSchedulePage() {
  const ready = useRequireRole("doctor");
  const router = useRouter();

  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [leaves, setLeaves] = useState<DoctorLeave[]>([]);
  const [loading, setLoading] = useState(true);

  const [leaveDate, setLeaveDate] = useState("");
  const [leaveReason, setLeaveReason] = useState("");
  const [submittingLeave, setSubmittingLeave] = useState(false);

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
      setLoading(true);
      const meData = await fetchDoctorMe();
      if (meData.doctor) {
        setDoctor(meData.doctor);
        const leaveData = await fetchDoctorLeave(meData.doctor.id);
        setLeaves(leaveData);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load doctor profile";
      showToast("failed", "Error loading profile", msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (ready) {
      loadData();
    }
  }, [ready, loadData]);

  const handleMarkLeave = async (e: FormEvent) => {
    e.preventDefault();
    if (!doctor || !leaveDate) return;

    try {
      setSubmittingLeave(true);
      const res = await markDoctorLeave(doctor.id, {
        leave_date: leaveDate,
        reason: leaveReason.trim() || undefined,
      });

      const affected = (res as unknown as { affected_appointments_count?: number }).affected_appointments_count || 0;
      showToast(
        "success",
        "Leave marked",
        affected > 0 ? `Marked leave for ${leaveDate}. ${affected} appointment(s) cancelled.` : `Marked leave for ${leaveDate}.`
      );

      setLeaveDate("");
      setLeaveReason("");
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to mark leave";
      showToast("failed", "Error marking leave", msg);
    } finally {
      setSubmittingLeave(false);
    }
  };

  const handleDeleteLeave = async (leaveId: number) => {
    if (!doctor) return;
    try {
      await deleteDoctorLeave(doctor.id, leaveId);
      showToast("success", "Leave removed", "Leave date removed successfully.");
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to remove leave";
      showToast("failed", "Error removing leave", msg);
    }
  };

  if (!ready || loading) return null;

  return (
    <AppShell
      role="doctor"
      onLogout={() => {
        clearSession();
        router.push("/login");
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        {toast && <Toast variant={toast.variant} title={toast.title}>{toast.body}</Toast>}

        <div>
          <h1>Doctor Schedule & Leave Management</h1>
          <p style={{ color: "var(--color-slate)", margin: 0 }}>
            Manage practice schedule settings and mark scheduled leave dates.
          </p>
        </div>

        <VitalsLine tone="sage" animate />

        <Card>
          <h2>Mark Scheduled Leave</h2>
          <form onSubmit={handleMarkLeave} style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
              <Input
                label="Leave Date"
                type="date"
                value={leaveDate}
                onChange={(e) => setLeaveDate(e.target.value)}
              />
              <Input
                label="Reason (Optional)"
                placeholder="e.g. Medical conference, Annual leave..."
                value={leaveReason}
                onChange={(e) => setLeaveReason(e.target.value)}
              />
            </div>
            <div>
              <Button type="submit" variant="primary" disabled={submittingLeave}>
                {submittingLeave ? "Marking Leave..." : "Mark Leave Date"}
              </Button>
            </div>
          </form>

          <div style={{ marginTop: "2rem" }}>
            <h3>Your Scheduled Leaves</h3>
            <Table
              rows={leaves}
              rowKey={(l) => l.id}
              emptyTitle="No leave dates scheduled."
              columns={[
                {
                  key: "date",
                  header: "Date",
                  render: (l) => <span style={{ fontFamily: "var(--font-mono)" }}>{l.leave_date}</span>,
                },
                {
                  key: "reason",
                  header: "Reason",
                  render: (l) => <span>{l.reason || "—"}</span>,
                },
                {
                  key: "actions",
                  header: "Action",
                  render: (l) => (
                    <div style={{ textAlign: "right" }}>
                      <Button size="sm" variant="ghost" onClick={() => handleDeleteLeave(l.id)}>
                        Remove
                      </Button>
                    </div>
                  ),
                },
              ]}
            />
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
