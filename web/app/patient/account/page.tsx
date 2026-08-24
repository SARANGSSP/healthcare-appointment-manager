"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../../components/shell/AppShell";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { Input } from "../../../components/ui/Input";
import { Toast, type ToastVariant } from "../../../components/ui/Toast";
import { VitalsLine } from "../../../components/ui/VitalsLine";
import { clearSession, fetchMe, updatePatientMe } from "../../../lib/api";
import { useRequireRole } from "../../../lib/useRequireRole";

export default function PatientAccountPage() {
  const ready = useRequireRole("patient");
  const router = useRouter();

  // Profile fields state
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [dob, setDob] = useState("");

  const [loading, setLoading] = useState(true);
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

  const loadProfile = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchMe();
      setEmail(data.email || "");
      if (data.patient_profile) {
        setFullName(data.patient_profile.full_name || "");
        setPhone(data.patient_profile.phone || "");
        setDob(data.patient_profile.dob || "");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load account profile";
      showToast("failed", "Error loading profile", msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (ready) {
      loadProfile();
    }
  }, [ready, loadProfile]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await updatePatientMe({
        email: email.trim() || undefined,
        full_name: fullName.trim() || undefined,
        phone: phone.trim() || undefined,
        dob: dob.trim() || undefined,
      });
      showToast("success", "Profile Updated", "Your account settings have been saved.");
      loadProfile();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save profile";
      showToast("failed", "Error saving profile", msg);
    } finally {
      setSubmitting(false);
    }
  };

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
        {toast && <Toast variant={toast.variant} title={toast.title}>{toast.body}</Toast>}

        <div>
          <h1>Patient Account & Preferences</h1>
          <p style={{ color: "var(--color-slate)", margin: 0 }}>
            Manage notification preferences and account settings.
          </p>
        </div>

        <VitalsLine tone="sage" />

        <Card>
          <h2>Account Details</h2>
          {loading ? (
            <p style={{ color: "var(--color-slate)", textAlign: "center", padding: "1rem" }}>Loading settings...</p>
          ) : (
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1rem" }}>
              <Input
                label="Email Address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <Input
                label="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />

              <Input
                label="Phone Number"
                type="tel"
                placeholder="e.g. +1 555-0199"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />

              <Input
                label="Date of Birth"
                type="date"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
              />

              <div style={{ display: "flex", gap: "1rem", alignItems: "center", marginTop: "1rem" }}>
                <Button type="submit" variant="primary" disabled={submitting}>
                  {submitting ? "Saving..." : "Save Preferences"}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    clearSession();
                    router.push("/login");
                  }}
                >
                  Sign Out
                </Button>
              </div>
            </form>
          )}
        </Card>
      </div>
    </AppShell>
  );
}
