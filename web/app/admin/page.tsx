"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../components/shell/AppShell";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Table } from "../../components/ui/Table";

import { Toast, type ToastVariant } from "../../components/ui/Toast";
import { VitalsLine } from "../../components/ui/VitalsLine";
import {
  clearSession,
  createDoctor,
  deleteDoctor,
  fetchAdminNotifications,
  fetchAdminOverview,
  fetchDoctors,
  retryNotification,
  updateDoctor,
  type Doctor,
} from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

export default function AdminPortal() {
  const ready = useRequireRole("admin");
  const router = useRouter();

  // Overview metrics state
  const [overview, setOverview] = useState<{
    total_bookings: number;
    active_doctors: number;
    total_patients: number;
    failed_notifications: number;
    system_status: string;
  } | null>(null);

  // Doctors management state
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loadingDoctors, setLoadingDoctors] = useState(true);

  // Notifications state
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

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [editDoctor, setEditDoctor] = useState<Doctor | null>(null);
  const [deleteDoctorId, setDeleteDoctorId] = useState<number | null>(null);

  // Form input state
  const [fullName, setFullName] = useState("");
  const [specialisation, setSpecialisation] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [slotDuration, setSlotDuration] = useState(20);
  const [submitting, setSubmitting] = useState(false);

  // Toast state
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
      setLoadingDoctors(true);
      const [docData, ovData, notifData] = await Promise.all([
        fetchDoctors(),
        fetchAdminOverview().catch(() => null),
        fetchAdminNotifications().catch(() => []),
      ]);
      setDoctors(docData);
      if (ovData) setOverview(ovData);
      setNotifications(notifData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load admin data";
      showToast("failed", "Error loading data", msg);
    } finally {
      setLoadingDoctors(false);
    }
  }, []);

  useEffect(() => {
    if (ready) {
      loadData();
    }
  }, [ready, loadData]);

  const handleAddSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await createDoctor({
        full_name: fullName,
        specialisation,
        email,
        password,
        slot_duration_minutes: Number(slotDuration) || 20,
      });
      showToast("success", "Doctor Profile Created", `Dr. ${fullName} has been added.`);
      setShowAddModal(false);
      resetForm();
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create doctor";
      showToast("failed", "Error creating doctor", msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!editDoctor) return;
    try {
      setSubmitting(true);
      await updateDoctor(editDoctor.id, {
        full_name: fullName,
        specialisation,
        email,
        slot_duration_minutes: Number(slotDuration) || 20,
      });
      showToast("success", "Doctor Profile Updated", `Dr. ${fullName}'s profile updated.`);
      setEditDoctor(null);
      resetForm();
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update doctor";
      showToast("failed", "Error updating doctor", msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteDoctorId) return;
    try {
      await deleteDoctor(deleteDoctorId);
      showToast("success", "Doctor Deleted", "Doctor profile removed successfully.");
      setDeleteDoctorId(null);
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete doctor";
      showToast("failed", "Error deleting doctor", msg);
    }
  };

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

  const resetForm = () => {
    setFullName("");
    setSpecialisation("");
    setEmail("");
    setPassword("");
    setSlotDuration(20);
  };

  const openEditModal = (doc: Doctor) => {
    setEditDoctor(doc);
    setFullName(doc.full_name);
    setSpecialisation(doc.specialisation);
    setEmail(doc.email || "");

    setSlotDuration(doc.slot_duration_minutes);
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

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
          <div>
            <h1>Admin Dashboard</h1>
            <p style={{ color: "var(--color-slate)", margin: 0 }}>
              System overview, doctor profile management, and notification delivery logs.
            </p>
          </div>
          <Button
            variant="primary"
            onClick={() => {
              resetForm();
              setShowAddModal(true);
            }}
          >
            + Add Doctor Profile
          </Button>
        </div>

        <VitalsLine tone="sage" animate />

        {/* OVERVIEW METRICS CARDS (Chunk 18) */}
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

        {/* DOCTOR MANAGEMENT TABLE (Chunk 5) */}
        <Card>
          <h2>Doctor Profiles</h2>
          {loadingDoctors ? (
            <p style={{ color: "var(--color-slate)", textAlign: "center", padding: "1rem" }}>Loading doctor profiles...</p>
          ) : (
            <Table
              rows={doctors}
              rowKey={(doc) => doc.id}
              emptyTitle="No doctor profiles configured yet."
              columns={[
                {
                  key: "name",
                  header: "Doctor Name",
                  render: (doc) => <span style={{ fontWeight: 600 }}>{doc.full_name}</span>,
                },
                {
                  key: "specialisation",
                  header: "Specialisation",
                  render: (doc) => <Badge tone="sage">{doc.specialisation}</Badge>,
                },
                {
                  key: "email",
                  header: "Email",
                  render: (doc) => (
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.875rem" }}>{doc.email}</span>
                  ),
                },
                {
                  key: "slot_duration",
                  header: "Slot Duration",
                  render: (doc) => (
                    <span style={{ fontFamily: "var(--font-mono)" }}>{doc.slot_duration_minutes} min</span>
                  ),
                },
                {
                  key: "actions",
                  header: "Actions",
                  render: (doc) => (
                    <div style={{ textAlign: "right" }}>
                      <Button size="sm" variant="secondary" onClick={() => openEditModal(doc)} style={{ marginRight: "0.5rem" }}>
                        Edit
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setDeleteDoctorId(doc.id)}>
                        Delete
                      </Button>
                    </div>
                  ),
                },
              ]}
            />
          )}
        </Card>

        {/* NOTIFICATION MONITORING TABLE (Chunk 14) */}
        <Card>
          <h2>System Notification Delivery Logs</h2>
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


        {/* ADD DOCTOR MODAL */}
        {showAddModal && (
          <div className="modal-overlay">
            <div className="modal-dialog">
              <div className="modal-header">
                <h2>Add Doctor Profile</h2>
                <button type="button" onClick={() => setShowAddModal(false)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1.25rem" }}>
                  &times;
                </button>
              </div>
              <form onSubmit={handleAddSubmit} style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                <Input label="Full Name" placeholder="Dr. Jane Smith" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
                <Input label="Specialisation" placeholder="Cardiology" value={specialisation} onChange={(e) => setSpecialisation(e.target.value)} required />
                <Input label="Email Address" type="email" placeholder="jane.smith@clinic.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
                <Input label="Password" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required />
                <Input label="Slot Duration (Minutes)" type="number" value={slotDuration.toString()} onChange={(e) => setSlotDuration(Number(e.target.value))} required />

                <div className="modal-footer" style={{ marginTop: "1rem" }}>
                  <Button type="button" variant="secondary" onClick={() => setShowAddModal(false)}>Cancel</Button>
                  <Button type="submit" variant="primary" disabled={submitting}>{submitting ? "Creating..." : "Save Doctor Profile"}</Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* EDIT DOCTOR MODAL */}
        {editDoctor && (
          <div className="modal-overlay">
            <div className="modal-dialog">
              <div className="modal-header">
                <h2>Edit Doctor Profile</h2>
                <button type="button" onClick={() => setEditDoctor(null)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1.25rem" }}>
                  &times;
                </button>
              </div>
              <form onSubmit={handleEditSubmit} style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                <Input label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
                <Input label="Specialisation" value={specialisation} onChange={(e) => setSpecialisation(e.target.value)} required />
                <Input label="Email Address" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                <Input label="Slot Duration (Minutes)" type="number" value={slotDuration.toString()} onChange={(e) => setSlotDuration(Number(e.target.value))} required />

                <div className="modal-footer" style={{ marginTop: "1rem" }}>
                  <Button type="button" variant="secondary" onClick={() => setEditDoctor(null)}>Cancel</Button>
                  <Button type="submit" variant="primary" disabled={submitting}>{submitting ? "Saving..." : "Update Profile"}</Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* DELETE CONFIRMATION MODAL */}
        {deleteDoctorId && (
          <div className="modal-overlay">
            <div className="modal-dialog" style={{ maxWidth: "400px" }}>
              <div className="modal-header">
                <h2>Confirm Deletion</h2>
              </div>
              <p style={{ color: "var(--color-slate)", marginTop: "0.5rem" }}>
                Are you sure you want to delete this doctor profile? This action will remove their account and schedule.
              </p>
              <div className="modal-footer" style={{ marginTop: "1rem" }}>
                <Button variant="secondary" onClick={() => setDeleteDoctorId(null)}>Cancel</Button>
                <Button variant="primary" onClick={handleDeleteConfirm}>Confirm Delete</Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
