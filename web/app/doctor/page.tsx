"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../components/shell/AppShell";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Table, type TableColumn } from "../../components/ui/Table";
import { Toast, type ToastVariant } from "../../components/ui/Toast";
import { VitalsLine } from "../../components/ui/VitalsLine";
import {
  clearSession,
  deleteDoctorLeave,
  fetchDoctorLeave,
  fetchDoctorMe,
  markDoctorLeave,
  type Doctor,
  type DoctorLeave,
} from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

export default function DoctorHome() {
  const ready = useRequireRole("doctor");
  const router = useRouter();

  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [leaves, setLeaves] = useState<DoctorLeave[]>([]);
  const [loading, setLoading] = useState(true);

  // Leave Form state
  const [leaveDate, setLeaveDate] = useState("");
  const [leaveReason, setLeaveReason] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Toast notification state
  const [toast, setToast] = useState<{
    variant: ToastVariant;
    title: string;
    body?: string;
  } | null>(null);

  const showToast = (variant: ToastVariant, title: string, body?: string) => {
    setToast({ variant, title, body });
    setTimeout(() => setToast(null), 4000);
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const meRes = await fetchDoctorMe();
      if (meRes.doctor) {
        setDoctor(meRes.doctor);
        const leaveData = await fetchDoctorLeave(meRes.doctor.id);
        setLeaves(leaveData);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load doctor profile";
      showToast("failed", "Error loading data", msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (ready) {
      loadData();
    }
  }, [ready, loadData]);

  const handleMarkLeaveSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!doctor) return;
    setFormError(null);

    if (!leaveDate) {
      setFormError("Please select a date for your leave.");
      return;
    }

    try {
      setSubmitting(true);
      await markDoctorLeave(doctor.id, {
        leave_date: leaveDate,
        reason: leaveReason.trim() || undefined,
      });
      showToast("success", "Leave date marked", `Leave for ${leaveDate} has been saved.`);
      setLeaveDate("");
      setLeaveReason("");
      // Reload leave list
      const updatedLeaves = await fetchDoctorLeave(doctor.id);
      setLeaves(updatedLeaves);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to mark leave date";
      setFormError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemoveLeave = async (leaveId: number, dateStr: string) => {
    if (!doctor) return;
    try {
      await deleteDoctorLeave(doctor.id, leaveId);
      showToast("success", "Leave date removed", `Leave for ${dateStr} has been cancelled.`);
      const updatedLeaves = await fetchDoctorLeave(doctor.id);
      setLeaves(updatedLeaves);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to remove leave";
      showToast("failed", "Error removing leave", msg);
    }
  };

  if (!ready) return null;

  const leaveColumns: TableColumn<DoctorLeave>[] = [
    {
      key: "leave_date",
      header: "Leave Date",
      render: (item) => (
        <strong style={{ fontFamily: "var(--font-mono)", fontSize: "0.9375rem" }}>
          {item.leave_date}
        </strong>
      ),
    },
    {
      key: "reason",
      header: "Reason",
      render: (item) => (
        <span style={{ color: item.reason ? "var(--color-ink)" : "var(--color-slate)" }}>
          {item.reason || "No reason specified"}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: () => <Badge variant="amber">Marked Off</Badge>,
    },
    {
      key: "actions",
      header: "Actions",
      render: (item) => (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => handleRemoveLeave(item.id, item.leave_date)}
        >
          Remove
        </Button>
      ),
    },
  ];

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
            {doctor
              ? `Welcome, Dr. ${doctor.full_name} (${doctor.specialisation})`
              : "Manage your working schedule and mark upcoming leave dates."}
          </p>
        </div>

        <VitalsLine tone="ink" />

        {loading ? (
          <Card>
            <p style={{ color: "var(--color-slate)", textAlign: "center", padding: "2rem" }}>
              Loading schedule & profile details...
            </p>
          </Card>
        ) : (
          <>
            {/* Practice Schedule Summary Card */}
            <Card>
              <h2>Practice Hours & Consultation Settings</h2>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: "1rem",
                  marginTop: "0.5rem",
                }}
              >
                <div>
                  <span style={{ fontSize: "0.8125rem", color: "var(--color-slate)", display: "block" }}>
                    Specialisation
                  </span>
                  <strong>{doctor?.specialisation || "General"}</strong>
                </div>
                <div>
                  <span style={{ fontSize: "0.8125rem", color: "var(--color-slate)", display: "block" }}>
                    Slot Duration
                  </span>
                  <strong style={{ fontFamily: "var(--font-mono)" }}>
                    {doctor?.slot_duration_minutes || 20} minutes per consultation
                  </strong>
                </div>
                <div>
                  <span style={{ fontSize: "0.8125rem", color: "var(--color-slate)", display: "block" }}>
                    Working Days
                  </span>
                  <span>Mon – Fri (09:00–13:00, 14:00–17:00)</span>
                </div>
              </div>
            </Card>

            {/* Mark Leave Form Card */}
            <Card>
              <h2>Mark Upcoming Leave Date</h2>
              <p style={{ fontSize: "0.875rem", color: "var(--color-slate)" }}>
                Select a date when you will be unavailable for appointments.
              </p>

              <form
                onSubmit={handleMarkLeaveSubmit}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "1rem",
                  maxWidth: "500px",
                  marginTop: "1rem",
                }}
              >
                {formError && <p className="field-error">{formError}</p>}

                <Input
                  label="Leave Date"
                  type="date"
                  value={leaveDate}
                  onChange={(e) => setLeaveDate(e.target.value)}
                  required
                />

                <Input
                  label="Reason (Optional)"
                  placeholder="e.g. Vacation, Annual Conference"
                  value={leaveReason}
                  onChange={(e) => setLeaveReason(e.target.value)}
                />

                <div>
                  <Button type="submit" variant="primary" disabled={submitting}>
                    {submitting ? "Saving..." : "Mark Leave Date"}
                  </Button>
                </div>
              </form>
            </Card>

            {/* Marked Leave List Table */}
            <Card>
              <h2>Scheduled Leave Dates</h2>
              <Table
                columns={leaveColumns}
                rows={leaves}
                rowKey={(item) => item.id}
                emptyTitle="No leave dates currently scheduled"
              />
            </Card>
          </>
        )}
      </div>
    </AppShell>
  );
}
