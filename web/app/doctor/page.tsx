"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../components/shell/AppShell";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/Table";
import { TextArea } from "../../components/ui/TextArea";
import { Toast, type ToastVariant } from "../../components/ui/Toast";
import { VitalsLine } from "../../components/ui/VitalsLine";
import {
  clearSession,
  deleteDoctorLeave,
  fetchDoctorLeave,
  fetchDoctorMe,
  fetchTodayQueue,
  markDoctorLeave,
  submitVisitNotes,
  type Appointment,
  type Doctor,
  type DoctorLeave,
  type PrescriptionInputItem,
} from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

export default function DoctorPortal() {
  const ready = useRequireRole("doctor");
  const router = useRouter();

  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [leaves, setLeaves] = useState<DoctorLeave[]>([]);
  const [loading, setLoading] = useState(true);

  // Queue state
  const [queue, setQueue] = useState<Appointment[]>([]);
  const [loadingQueue, setLoadingQueue] = useState(true);

  // Leave marking form state
  const [leaveDate, setLeaveDate] = useState("");
  const [leaveReason, setLeaveReason] = useState("");
  const [submittingLeave, setSubmittingLeave] = useState(false);

  // Visit notes form modal state
  const [selectedAppt, setSelectedAppt] = useState<Appointment | null>(null);
  const [clinicalNotes, setClinicalNotes] = useState("");
  const [medName, setMedName] = useState("");
  const [medDosage, setMedDosage] = useState("1 tablet");
  const [medFreq, setMedFreq] = useState("Daily after meals");
  const [medDays, setMedDays] = useState(5);
  const [prescriptions, setPrescriptions] = useState<PrescriptionInputItem[]>([]);
  const [submittingNotes, setSubmittingNotes] = useState(false);

  // Toast notification state
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

  const loadQueueData = useCallback(async () => {
    try {
      setLoadingQueue(true);
      const queueData = await fetchTodayQueue();
      setQueue(queueData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load queue";
      showToast("failed", "Error loading today queue", msg);
    } finally {
      setLoadingQueue(false);
    }
  }, []);

  useEffect(() => {
    if (ready) {
      loadData();
      loadQueueData();
    }
  }, [ready, loadData, loadQueueData]);

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
      loadQueueData();
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

  const handleAddPrescriptionItem = () => {
    if (!medName.trim()) return;
    setPrescriptions([
      ...prescriptions,
      {
        medication_name: medName.trim(),
        dosage: medDosage.trim(),
        frequency: medFreq.trim(),
        duration_days: Number(medDays) || 5,
      },
    ]);
    setMedName("");
  };

  const handleRemovePrescriptionItem = (index: number) => {
    setPrescriptions(prescriptions.filter((_, i) => i !== index));
  };

  const handleSubmitVisitNotes = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedAppt || !clinicalNotes.trim()) return;

    try {
      setSubmittingNotes(true);
      await submitVisitNotes(selectedAppt.id, {
        clinical_notes: clinicalNotes.trim(),
        prescriptions: prescriptions.length > 0 ? prescriptions : undefined,
      });

      showToast("success", "Visit Notes Saved", "Post-visit summary generated and appointment completed.");
      setSelectedAppt(null);
      setClinicalNotes("");
      setPrescriptions([]);
      loadQueueData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save visit notes";
      showToast("failed", "Error saving visit notes", msg);
    } finally {
      setSubmittingNotes(false);
    }
  };

  const getUrgencyBadge = (urgency?: "Low" | "Medium" | "High") => {
    switch (urgency) {
      case "High":
        return <Badge variant="coral">HIGH URGENCY</Badge>;
      case "Medium":
        return <Badge variant="amber">MEDIUM URGENCY</Badge>;
      default:
        return <Badge variant="sage">LOW URGENCY</Badge>;
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
          <h1>Doctor Portal</h1>
          <p style={{ color: "var(--color-slate)", margin: 0 }}>
            Welcome back, Dr. {doctor?.full_name || "Doctor"}. Manage your queue and leave schedule.
          </p>
        </div>

        <VitalsLine tone="sage" animate />

        {/* TODAY'S APPOINTMENT QUEUE CARD (Chunk 12 & 13) */}
        <Card className="card-elevated">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap" }}>
            <div>
              <h2>Today's Consultation Queue</h2>
              <p style={{ fontSize: "0.875rem", color: "var(--color-slate)", margin: 0 }}>
                Time-ordered patient queue with AI pre-visit urgency triage
              </p>
            </div>
            <Badge variant="sage">{queue.length} Patients Scheduled</Badge>
          </div>

          <div style={{ marginTop: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
            {loadingQueue ? (
              <p style={{ color: "var(--color-slate)", textAlign: "center", padding: "1rem" }}>Loading queue...</p>
            ) : queue.length === 0 ? (
              <p style={{ color: "var(--color-slate)", textAlign: "center", padding: "1rem" }}>
                No appointments scheduled for today.
              </p>
            ) : (
              queue.map((appt) => (
                <div
                  key={appt.id}
                  style={{
                    padding: "1.25rem",
                    borderRadius: "var(--radius-control)",
                    border: "1px solid var(--color-border)",
                    background: appt.status === "completed" ? "var(--color-paper)" : "var(--color-paper-raised)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.75rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap" }}>
                    <div>
                      <strong style={{ fontSize: "1.125rem" }}>{appt.patient_name}</strong>
                      <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.875rem", color: "var(--color-slate)", marginLeft: "0.75rem" }}>
                        {appt.slot_start} – {appt.slot_end}
                      </span>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      {getUrgencyBadge(appt.symptom_summary?.urgency)}
                      <Badge variant={appt.status === "completed" ? "sage" : "ink"}>
                        {appt.status.toUpperCase()}
                      </Badge>
                    </div>
                  </div>

                  {/* Pre-visit AI Summary Card */}
                  {appt.symptom_summary && (
                    <div style={{ background: "var(--color-paper)", padding: "0.875rem", borderRadius: "var(--radius-control)", border: "1px solid var(--color-border)" }}>
                      <strong style={{ fontSize: "0.875rem", display: "block", color: "var(--color-ink)" }}>
                        AI Pre-Visit Triage & Chief Complaint
                      </strong>
                      <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.9375rem" }}>
                        {appt.symptom_summary.chief_complaint}
                      </p>

                      {appt.symptom_summary.suggested_questions.length > 0 && (
                        <div style={{ marginTop: "0.5rem" }}>
                          <span style={{ fontSize: "0.75rem", color: "var(--color-slate)", display: "block" }}>
                            Suggested Questions for Consultation:
                          </span>
                          <ul style={{ margin: "0.25rem 0 0 1.25rem", padding: 0, fontSize: "0.875rem" }}>
                            {appt.symptom_summary.suggested_questions.map((q, idx) => (
                              <li key={idx}>{q}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Visit Notes Action */}
                  <div style={{ display: "flex", justifyContent: "flex-end" }}>
                    <Button
                      size="sm"
                      variant={appt.status === "completed" ? "secondary" : "primary"}
                      onClick={() => {
                        setSelectedAppt(appt);
                        setClinicalNotes(appt.visit_note?.clinical_notes || "");
                        setPrescriptions(appt.visit_note?.prescriptions || []);
                      }}
                    >
                      {appt.status === "completed" ? "View / Edit Visit Notes" : "Start Visit & Notes"}
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* CLINICAL VISIT NOTES MODAL */}
        {selectedAppt && (
          <div className="modal-overlay">
            <div className="modal-dialog" style={{ maxWidth: "600px" }}>
              <div className="modal-header">
                <h2>Clinical Visit Notes — {selectedAppt.patient_name}</h2>
                <button
                  type="button"
                  style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1.25rem" }}
                  onClick={() => setSelectedAppt(null)}
                >
                  &times;
                </button>
              </div>

              <form onSubmit={handleSubmitVisitNotes} style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                <TextArea
                  label="Clinical Observations & Diagnosis"
                  placeholder="e.g. Patient presents with acute bronchitis. Lungs clear to auscultation. Advised rest..."
                  value={clinicalNotes}
                  onChange={(e) => setClinicalNotes(e.target.value)}
                  hint="These notes are processed by AI into a patient-friendly summary."
                />

                <div>
                  <h3>Add Prescription Items</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", marginTop: "0.5rem" }}>
                    <Input label="Medication Name" placeholder="Amoxicillin" value={medName} onChange={(e) => setMedName(e.target.value)} />
                    <Input label="Dosage" placeholder="500mg" value={medDosage} onChange={(e) => setMedDosage(e.target.value)} />
                    <Input label="Frequency" placeholder="Twice daily after meals" value={medFreq} onChange={(e) => setMedFreq(e.target.value)} />
                    <Input label="Duration (Days)" type="number" value={medDays.toString()} onChange={(e) => setMedDays(Number(e.target.value))} />
                  </div>

                  <div style={{ marginTop: "0.5rem" }}>
                    <Button type="button" size="sm" variant="secondary" onClick={handleAddPrescriptionItem}>
                      + Add Medication
                    </Button>
                  </div>

                  {prescriptions.length > 0 && (
                    <div style={{ marginTop: "0.75rem", display: "flex", flexDirection: "column", gap: "0.375rem" }}>
                      {prescriptions.map((p, idx) => (
                        <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--color-paper)", padding: "0.5rem", borderRadius: "var(--radius-control)" }}>
                          <span style={{ fontSize: "0.875rem" }}>
                            <strong>{p.medication_name}</strong> ({p.dosage}) — {p.frequency} for {p.duration_days} days
                          </span>
                          <Button size="sm" variant="ghost" type="button" onClick={() => handleRemovePrescriptionItem(idx)}>
                            Remove
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="modal-footer" style={{ marginTop: "1rem" }}>
                  <Button type="button" variant="secondary" onClick={() => setSelectedAppt(null)}>
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={submittingNotes}>
                    {submittingNotes ? "Saving..." : "Save Visit & Generate Patient Summary"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* PRACTICE SCHEDULE & LEAVE MANAGEMENT CARD */}
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
            {leaves.length === 0 ? (
              <p style={{ color: "var(--color-slate)", marginTop: "0.5rem" }}>No leave dates scheduled.</p>
            ) : (
              <Table style={{ marginTop: "0.75rem" }}>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Reason</TableHead>
                    <TableHead style={{ textAlign: "right" }}>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leaves.map((l) => (
                    <TableRow key={l.id}>
                      <TableCell style={{ fontFamily: "var(--font-mono)" }}>{l.leave_date}</TableCell>
                      <TableCell>{l.reason || "—"}</TableCell>
                      <TableCell style={{ textAlign: "right" }}>
                        <Button size="sm" variant="ghost" onClick={() => handleDeleteLeave(l.id)}>
                          Remove
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
