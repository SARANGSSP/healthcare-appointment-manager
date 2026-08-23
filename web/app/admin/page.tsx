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
  createDoctor,
  deleteDoctor,
  fetchDoctors,
  updateDoctor,
  type Doctor,
} from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

const DEFAULT_WORKING_HOURS = {
  mon: ["09:00-13:00", "14:00-17:00"],
  tue: ["09:00-13:00", "14:00-17:00"],
  wed: ["09:00-13:00", "14:00-17:00"],
  thu: ["09:00-13:00", "14:00-17:00"],
  fri: ["09:00-13:00", "14:00-17:00"],
};

export default function AdminHome() {
  const ready = useRequireRole("admin");
  const router = useRouter();

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);

  // Toast notification state
  const [toast, setToast] = useState<{
    variant: ToastVariant;
    title: string;
    body?: string;
  } | null>(null);

  // Modal states
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingDoctor, setEditingDoctor] = useState<Doctor | null>(null);
  const [deletingDoctor, setDeletingDoctor] = useState<Doctor | null>(null);

  // Form inputs state
  const [formEmail, setFormEmail] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formFullName, setFormFullName] = useState("");
  const [formSpecialisation, setFormSpecialisation] = useState("");
  const [formSlotDuration, setFormSlotDuration] = useState("20");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const showToast = (variant: ToastVariant, title: string, body?: string) => {
    setToast({ variant, title, body });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  const loadDoctors = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchDoctors();
      setDoctors(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load doctors";
      showToast("failed", "Error loading doctors", msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (ready) {
      loadDoctors();
    }
  }, [ready, loadDoctors]);

  const openAddModal = () => {
    setFormEmail("");
    setFormPassword("");
    setFormFullName("");
    setFormSpecialisation("General Medicine");
    setFormSlotDuration("20");
    setFormError(null);
    setIsAddOpen(true);
  };

  const openEditModal = (doc: Doctor) => {
    setEditingDoctor(doc);
    setFormEmail(doc.email || "");
    setFormPassword(""); // Password not updated on edit unless provided
    setFormFullName(doc.full_name);
    setFormSpecialisation(doc.specialisation);
    setFormSlotDuration(String(doc.slot_duration_minutes));
    setFormError(null);
  };

  const handleCreateSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formEmail.trim()) {
      setFormError("Email address is required.");
      return;
    }
    if (formPassword.length < 8) {
      setFormError("Password must be at least 8 characters.");
      return;
    }
    if (!formFullName.trim()) {
      setFormError("Full name is required.");
      return;
    }
    if (!formSpecialisation.trim()) {
      setFormError("Specialisation is required.");
      return;
    }

    const duration = parseInt(formSlotDuration, 10);
    if (isNaN(duration) || duration <= 0) {
      setFormError("Slot duration must be a positive number.");
      return;
    }

    try {
      setSubmitting(true);
      await createDoctor({
        email: formEmail.trim(),
        password: formPassword,
        full_name: formFullName.trim(),
        specialisation: formSpecialisation.trim(),
        slot_duration_minutes: duration,
        working_hours: DEFAULT_WORKING_HOURS,
      });
      showToast("success", "Doctor profile created", `Dr. ${formFullName} was successfully added.`);
      setIsAddOpen(false);
      loadDoctors();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create doctor profile";
      setFormError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!editingDoctor) return;
    setFormError(null);

    if (!formFullName.trim()) {
      setFormError("Full name is required.");
      return;
    }
    if (!formSpecialisation.trim()) {
      setFormError("Specialisation is required.");
      return;
    }

    const duration = parseInt(formSlotDuration, 10);
    if (isNaN(duration) || duration <= 0) {
      setFormError("Slot duration must be a positive number.");
      return;
    }

    try {
      setSubmitting(true);
      await updateDoctor(editingDoctor.id, {
        email: formEmail.trim() || undefined,
        full_name: formFullName.trim(),
        specialisation: formSpecialisation.trim(),
        slot_duration_minutes: duration,
      });
      showToast("success", "Doctor profile updated", `Dr. ${formFullName}'s profile was updated.`);
      setEditingDoctor(null);
      loadDoctors();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update doctor profile";
      setFormError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deletingDoctor) return;
    try {
      setSubmitting(true);
      await deleteDoctor(deletingDoctor.id);
      showToast("success", "Doctor deleted", `Dr. ${deletingDoctor.full_name} has been removed.`);
      setDeletingDoctor(null);
      loadDoctors();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete doctor";
      showToast("failed", "Delete failed", msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (!ready) return null;

  const columns: TableColumn<Doctor>[] = [
    {
      key: "name",
      header: "Doctor Name & Email",
      render: (doc) => (
        <div>
          <strong style={{ display: "block" }}>{doc.full_name}</strong>
          <span style={{ fontSize: "0.8125rem", color: "var(--color-slate)" }}>
            {doc.email || "No email"}
          </span>
        </div>
      ),
    },
    {
      key: "specialisation",
      header: "Specialisation",
      render: (doc) => <Badge variant="info">{doc.specialisation}</Badge>,
    },
    {
      key: "slot_duration",
      header: "Slot Duration",
      render: (doc) => (
        <span style={{ fontFamily: "var(--font-mono)" }}>
          {doc.slot_duration_minutes} mins
        </span>
      ),
    },
    {
      key: "working_hours",
      header: "Working Hours",
      render: (doc) => {
        const days = Object.keys(doc.working_hours || {});
        if (days.length === 0) return <span style={{ color: "var(--color-slate)" }}>Not set</span>;
        return (
          <span style={{ fontSize: "0.8125rem", color: "var(--color-slate)" }}>
            Mon-Fri (09:00-13:00, 14:00-17:00)
          </span>
        );
      },
    },
    {
      key: "actions",
      header: "Actions",
      render: (doc) => (
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Button
            size="sm"
            variant="secondary"
            onClick={(e) => {
              e.stopPropagation();
              openEditModal(doc);
            }}
          >
            Edit
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={(e) => {
              e.stopPropagation();
              setDeletingDoctor(doc);
            }}
          >
            Delete
          </Button>
        </div>
      ),
    },
  ];

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

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "var(--space-2)",
          }}
        >
          <div>
            <h1>Doctor Management</h1>
            <p style={{ color: "var(--color-slate)", margin: 0 }}>
              Manage doctor profiles, specialisations, and appointment slot durations.
            </p>
          </div>
          <Button variant="primary" onClick={openAddModal}>
            + Add Doctor
          </Button>
        </div>

        <VitalsLine tone="ink" />

        <Card>
          {loading ? (
            <p style={{ color: "var(--color-slate)", textAlign: "center", padding: "2rem" }}>
              Loading doctor profiles...
            </p>
          ) : (
            <Table
              columns={columns}
              rows={doctors}
              rowKey={(doc) => doc.id}
              emptyTitle="No doctor profiles created yet"
              emptyAction={
                <Button variant="primary" size="sm" onClick={openAddModal}>
                  + Add First Doctor
                </Button>
              }
            />
          )}
        </Card>
      </div>

      {/* Add Doctor Modal */}
      {isAddOpen && (
        <div className="modal-overlay" onClick={() => setIsAddOpen(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add New Doctor</h2>
              <Button variant="ghost" size="sm" onClick={() => setIsAddOpen(false)}>
                ✕
              </Button>
            </div>

            <form onSubmit={handleCreateSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {formError && <p className="field-error">{formError}</p>}

              <Input
                label="Full Name"
                placeholder="e.g. Dr. Sarah Mehta"
                value={formFullName}
                onChange={(e) => setFormFullName(e.target.value)}
                required
              />

              <Input
                label="Email Address"
                type="email"
                placeholder="doctor@clinic.com"
                value={formEmail}
                onChange={(e) => setFormEmail(e.target.value)}
                required
              />

              <Input
                label="Password"
                type="password"
                placeholder="At least 8 characters"
                value={formPassword}
                onChange={(e) => setFormPassword(e.target.value)}
                required
              />

              <Input
                label="Specialisation"
                placeholder="e.g. Cardiology, Pediatrics"
                value={formSpecialisation}
                onChange={(e) => setFormSpecialisation(e.target.value)}
                required
              />

              <Input
                label="Slot Duration (Minutes)"
                type="number"
                min="5"
                max="120"
                value={formSlotDuration}
                onChange={(e) => setFormSlotDuration(e.target.value)}
                hint="Default is 20 minutes per consultation slot."
                required
              />

              <div className="modal-footer">
                <Button type="button" variant="secondary" onClick={() => setIsAddOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={submitting}>
                  {submitting ? "Creating..." : "Save Doctor Profile"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Doctor Modal */}
      {editingDoctor && (
        <div className="modal-overlay" onClick={() => setEditingDoctor(null)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit Doctor Profile</h2>
              <Button variant="ghost" size="sm" onClick={() => setEditingDoctor(null)}>
                ✕
              </Button>
            </div>

            <form onSubmit={handleUpdateSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {formError && <p className="field-error">{formError}</p>}

              <Input
                label="Full Name"
                value={formFullName}
                onChange={(e) => setFormFullName(e.target.value)}
                required
              />

              <Input
                label="Email Address"
                type="email"
                value={formEmail}
                onChange={(e) => setFormEmail(e.target.value)}
                required
              />

              <Input
                label="Specialisation"
                value={formSpecialisation}
                onChange={(e) => setFormSpecialisation(e.target.value)}
                required
              />

              <Input
                label="Slot Duration (Minutes)"
                type="number"
                min="5"
                max="120"
                value={formSlotDuration}
                onChange={(e) => setFormSlotDuration(e.target.value)}
                required
              />

              <div className="modal-footer">
                <Button type="button" variant="secondary" onClick={() => setEditingDoctor(null)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={submitting}>
                  {submitting ? "Updating..." : "Update Doctor Profile"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingDoctor && (
        <div className="modal-overlay" onClick={() => setDeletingDoctor(null)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Confirm Doctor Deletion</h2>
              <Button variant="ghost" size="sm" onClick={() => setDeletingDoctor(null)}>
                ✕
              </Button>
            </div>

            <p>
              Are you sure you want to delete <strong>Dr. {deletingDoctor.full_name}</strong>?
              This action will remove their profile and user account from the system.
            </p>

            <div className="modal-footer">
              <Button type="button" variant="secondary" onClick={() => setDeletingDoctor(null)}>
                Cancel
              </Button>
              <Button
                type="button"
                variant="destructive"
                disabled={submitting}
                onClick={handleDeleteConfirm}
              >
                {submitting ? "Deleting..." : "Delete Doctor Profile"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
