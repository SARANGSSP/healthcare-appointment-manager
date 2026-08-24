"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../components/shell/AppShell";
import { Badge, UrgencyBadge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { TextArea } from "../../components/ui/TextArea";
import { Toast, type ToastVariant } from "../../components/ui/Toast";
import { VitalsLine } from "../../components/ui/VitalsLine";
import {
  cancelAppointment,
  clearSession,
  confirmBooking,
  fetchDoctorAvailability,
  fetchDoctors,
  holdSlot,
  fetchAppointmentSummary,
  fetchMyAppointments,
  type Appointment,
  type Doctor,
  type DoctorAvailability,
  type TimeSlot,
} from "../../lib/api";
import { useRequireRole } from "../../lib/useRequireRole";

export default function PatientHome() {
  const ready = useRequireRole("patient");
  const router = useRouter();

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loadingDoctors, setLoadingDoctors] = useState(true);

  // Search filter state
  const [specialisationFilter, setSpecialisationFilter] = useState("");

  // Selected doctor and availability state
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [availability, setAvailability] = useState<DoctorAvailability | null>(null);
  const [loadingAvailability, setLoadingAvailability] = useState(false);

  // Hold & Booking flow state
  const [heldAppointment, setHeldAppointment] = useState<Appointment | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState<number>(300);
  const [holdingSlot, setHoldingSlot] = useState(false);
  const [symptomsText, setSymptomsText] = useState("");
  const [confirming, setConfirming] = useState(false);

  // Active or Confirmed booking state
  const [confirmedAppointment, setConfirmedAppointment] = useState<Appointment | null>(null);

  // My appointments & summary modal states (M5 & H5)
  const [myAppointments, setMyAppointments] = useState<Appointment[]>([]);
  const [loadingMyAppointments, setLoadingMyAppointments] = useState(false);
  const [activeSummary, setActiveSummary] = useState<Appointment | null>(null);

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

  const loadDoctors = useCallback(async (spec?: string) => {
    try {
      setLoadingDoctors(true);
      const data = await fetchDoctors(spec);
      setDoctors(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load doctors";
      showToast("failed", "Error searching doctors", msg);
    } finally {
      setLoadingDoctors(false);
    }
  }, []);

  const loadMyAppointments = useCallback(async () => {
    try {
      setLoadingMyAppointments(true);
      const data = await fetchMyAppointments();
      setMyAppointments(data);
    } catch (err: unknown) {
      // ignore
    } finally {
      setLoadingMyAppointments(false);
    }
  }, []);

  useEffect(() => {
    if (ready) {
      loadDoctors();
      loadMyAppointments();
    }
  }, [ready, loadDoctors, loadMyAppointments]);

  const handleFilterChange = (val: string) => {
    setSpecialisationFilter(val);
    loadDoctors(val.trim() || undefined);
  };

  const loadAvailability = useCallback(
    async (docId: number, dateStr: string) => {
      try {
        setLoadingAvailability(true);
        const data = await fetchDoctorAvailability(docId, dateStr);
        setAvailability(data);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to compute availability";
        showToast("failed", "Error checking availability", msg);
      } finally {
        setLoadingAvailability(false);
      }
    },
    []
  );

  const handleSelectDoctor = (doc: Doctor) => {
    setSelectedDoctor(doc);
    setHeldAppointment(null);
    setConfirmedAppointment(null);
    loadAvailability(doc.id, selectedDate);
  };

  const handleDateChange = (newDate: string) => {
    setSelectedDate(newDate);
    setHeldAppointment(null);
    setConfirmedAppointment(null);
    if (selectedDoctor) {
      loadAvailability(selectedDoctor.id, newDate);
    }
  };

  // Hold slot handler
  const handleSlotClick = async (slot: TimeSlot) => {
    if (!selectedDoctor || slot.status !== "available" || holdingSlot) return;

    try {
      setHoldingSlot(true);
      const appt = await holdSlot({
        doctor_id: selectedDoctor.id,
        appt_date: selectedDate,
        slot_start: slot.start_time,
        slot_end: slot.end_time,
      });
      setHeldAppointment(appt);
      setRemainingSeconds(appt.ttl_seconds || 300);
      setSymptomsText("");
      showToast("info", "Slot held", `Slot ${slot.start_time}–${slot.end_time} is held for 5 minutes.`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Slot no longer available";
      showToast("failed", "Slot unavailable", msg);
      if (selectedDoctor) loadAvailability(selectedDoctor.id, selectedDate);
    } finally {
      setHoldingSlot(false);
    }
  };

  // Live 5-minute countdown timer effect
  useEffect(() => {
    if (!heldAppointment || heldAppointment.status !== "held") return;

    const timer = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setHeldAppointment(null);
          showToast("failed", "Hold expired", "Your slot hold has expired. Please select the slot again.");
          if (selectedDoctor) loadAvailability(selectedDoctor.id, selectedDate);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [heldAppointment, selectedDoctor, selectedDate, loadAvailability]);

  // Confirm booking handler
  const handleConfirmSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!heldAppointment) return;

    try {
      setConfirming(true);
      const confirmed = await confirmBooking(heldAppointment.id, {
        symptoms: symptomsText.trim() || undefined,
      });
      setConfirmedAppointment(confirmed);
      setHeldAppointment(null);
      showToast("success", "Appointment confirmed", `Your appointment with Dr. ${confirmed.doctor_name} is confirmed!`);
      if (selectedDoctor) loadAvailability(selectedDoctor.id, selectedDate);
      loadMyAppointments(); // M5 reload
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to confirm appointment";
      showToast("failed", "Booking failed", msg);
      setHeldAppointment(null);
      if (selectedDoctor) loadAvailability(selectedDoctor.id, selectedDate);
    } finally {
      setConfirming(false);
    }
  };

  // Cancel appointment handler (Chunk 10)
  const handleCancelClick = async (apptId: number) => {
    try {
      await cancelAppointment(apptId);
      showToast("info", "Appointment Cancelled", "Your appointment has been cancelled and the slot is released.");
      setConfirmedAppointment(null);
      if (selectedDoctor) loadAvailability(selectedDoctor.id, selectedDate);
      loadMyAppointments(); // M5 reload
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to cancel appointment";
      showToast("failed", "Cancellation failed", msg);
    }
  };

  const handleViewSummary = async (apptId: number) => {
    try {
      const summary = await fetchAppointmentSummary(apptId);
      setActiveSummary(summary);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load appointment summary";
      showToast("failed", "Error loading summary", msg);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
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
          <h1>Healthcare Appointments</h1>
          <p style={{ color: "var(--color-slate)", margin: 0 }}>
            Find a doctor, select an available slot, and manage your consultation.
          </p>
        </div>

        <VitalsLine tone="sage" animate={Boolean(confirmedAppointment)} />

        {/* Confirmed Appointment Banner Card & Post-Visit Summary (Chunk 10 & 13) */}
        {confirmedAppointment && (
          <Card style={{ borderColor: "var(--color-sage)", background: "var(--color-sage-tint)" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Badge tone={confirmedAppointment.status === "completed" ? "sage" : "sage"}>

                  {confirmedAppointment.status.toUpperCase()}
                </Badge>
                <strong style={{ color: "#3f5b44", fontSize: "1.125rem" }}>
                  Appointment Summary
                </strong>
              </div>

              <Button size="sm" variant="destructive" onClick={() => handleCancelClick(confirmedAppointment.id)}>
                Cancel Appointment
              </Button>
            </div>

            <div style={{ marginTop: "0.75rem", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              <p style={{ margin: 0 }}>
                <strong>Doctor:</strong> Dr. {confirmedAppointment.doctor_name} ({confirmedAppointment.specialisation})
              </p>
              <p style={{ margin: 0 }}>
                <strong>Date & Time:</strong> {confirmedAppointment.appt_date} at{" "}
                <span style={{ fontFamily: "var(--font-mono)" }}>
                  {confirmedAppointment.slot_start} – {confirmedAppointment.slot_end}
                </span>
              </p>
            </div>

            {/* Post-Visit Patient-Friendly AI Summary & Medication Schedule */}
            {confirmedAppointment.visit_note && (
              <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid var(--color-border)" }}>
                <strong style={{ color: "var(--color-ink)", display: "block" }}>Patient Care Summary</strong>
                <p style={{ fontSize: "0.9375rem", marginTop: "0.25rem" }}>
                  {confirmedAppointment.visit_note.patient_friendly_summary || confirmedAppointment.visit_note.clinical_notes}
                </p>

                {confirmedAppointment.visit_note.prescriptions.length > 0 && (
                  <div style={{ marginTop: "0.75rem" }}>
                    <span style={{ fontSize: "0.8125rem", color: "var(--color-slate)", display: "block" }}>
                      Prescription Medication Schedule:
                    </span>
                    <ul style={{ margin: "0.25rem 0 0 1.25rem", padding: 0, fontSize: "0.875rem" }}>
                      {confirmedAppointment.visit_note.prescriptions.map((p, idx) => (
                        <li key={idx}>
                          <strong>{p.medication_name}</strong> ({p.dosage}) — {p.frequency} for {p.duration_days} days
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <div style={{ marginTop: "1rem" }}>
              <Button size="sm" variant="secondary" onClick={() => setConfirmedAppointment(null)}>
                Book Another Appointment
              </Button>
            </div>
          </Card>
        )}

        {/* YOUR APPOINTMENTS SECTION (M5 & H5) */}
        <Card>
          <h2>Your Appointments</h2>
          <p style={{ fontSize: "0.875rem", color: "var(--color-slate)", margin: "0 0 1.25rem 0" }}>
            View your upcoming schedule, past consultations, and clinical summaries.
          </p>
          {loadingMyAppointments ? (
            <p style={{ color: "var(--color-slate)", textAlign: "center", padding: "1rem" }}>Loading appointments...</p>
          ) : myAppointments.length === 0 ? (
            <p style={{ color: "var(--color-slate)", textAlign: "center", padding: "1rem" }}>
              You don't have any appointments booked.
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {myAppointments.map((appt) => (
                <div
                  key={appt.id}
                  style={{
                    padding: "1rem",
                    borderRadius: "var(--radius-control)",
                    border: "1px solid var(--color-border)",
                    background: "var(--color-paper-raised)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: "0.75rem",
                  }}
                >
                  <div>
                    <strong style={{ fontSize: "1rem", display: "block" }}>
                      Dr. {appt.doctor_name} ({appt.specialisation})
                    </strong>
                    <span style={{ fontSize: "0.875rem", color: "var(--color-slate)", display: "block", marginTop: "0.25rem" }}>
                      {appt.appt_date} at <span style={{ fontFamily: "var(--font-mono)" }}>{appt.slot_start}–{appt.slot_end}</span>
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <Badge tone={appt.status === "completed" || appt.status === "confirmed" ? "sage" : appt.status === "held" ? "amber" : "coral"}>
                      {appt.status.toUpperCase()}
                    </Badge>
                    
                    <Button size="sm" variant="secondary" onClick={() => handleViewSummary(appt.id)}>
                      View Details
                    </Button>

                    {appt.status === "confirmed" && (
                      <Button size="sm" variant="destructive" onClick={() => handleCancelClick(appt.id)}>
                        Cancel
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Doctor Search Card */}
        <Card>
          <h2>Search Doctors</h2>
          <div style={{ marginTop: "0.75rem" }}>
            <Input
              label="Filter by Specialisation"
              placeholder="e.g. Cardiology, Neurology, Pediatrics..."
              value={specialisationFilter}
              onChange={(e) => handleFilterChange(e.target.value)}
            />
          </div>

          <div style={{ marginTop: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
            {loadingDoctors ? (
              <p style={{ color: "var(--color-slate)", textAlign: "center", padding: "1rem" }}>
                Searching doctors...
              </p>
            ) : doctors.length === 0 ? (
              <p style={{ color: "var(--color-slate)", textAlign: "center", padding: "1rem" }}>
                No doctors found matching "{specialisationFilter}".
              </p>
            ) : (
              doctors.map((doc) => (
                <div
                  key={doc.id}
                  style={{
                    padding: "1rem",
                    borderRadius: "var(--radius-control)",
                    border: "1px solid var(--color-border)",
                    background:
                      selectedDoctor?.id === doc.id
                        ? "var(--color-sage-tint)"
                        : "var(--color-paper-raised)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: "0.5rem",
                  }}
                >
                  <div>
                    <strong style={{ display: "block", fontSize: "1.0625rem" }}>
                      {doc.full_name}
                    </strong>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.25rem" }}>
                      <Badge tone="sage">{doc.specialisation}</Badge>
                      <span style={{ fontSize: "0.8125rem", color: "var(--color-slate)", fontFamily: "var(--font-mono)" }}>
                        {doc.slot_duration_minutes} min slots
                      </span>
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant={selectedDoctor?.id === doc.id ? "primary" : "secondary"}
                    onClick={() => handleSelectDoctor(doc)}
                  >
                    {selectedDoctor?.id === doc.id ? "Viewing Schedule" : "View Availability"}
                  </Button>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Selected Doctor Schedule & Slot Picker */}
        {selectedDoctor && !heldAppointment && (
          <Card>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap" }}>
              <div>
                <h2>{selectedDoctor.full_name}</h2>
                <p style={{ fontSize: "0.875rem", color: "var(--color-slate)", margin: 0 }}>
                  Select a slot for {selectedDate}
                </p>
              </div>
              <Button size="sm" variant="ghost" onClick={() => setSelectedDoctor(null)}>
                Close Schedule
              </Button>
            </div>

            <div style={{ marginTop: "1rem", maxWidth: "300px" }}>
              <Input
                label="Select Date"
                type="date"
                value={selectedDate}
                onChange={(e) => handleDateChange(e.target.value)}
              />
            </div>

            <div style={{ marginTop: "1.5rem" }}>
              {loadingAvailability ? (
                <p style={{ color: "var(--color-slate)", padding: "1rem 0" }}>
                  Computing free slots...
                </p>
              ) : availability?.on_leave ? (
                <div style={{ padding: "1rem", borderRadius: "var(--radius-control)", background: "var(--color-coral-tint)", border: "1px solid var(--color-coral)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <Badge tone="coral">ON LEAVE</Badge>
                    <strong style={{ color: "#a1432e" }}>Doctor unavailable on this date</strong>
                  </div>
                  {availability.leave_reason && (
                    <p style={{ margin: "0.5rem 0 0 0", fontSize: "0.875rem", color: "#a1432e" }}>
                      Reason: {availability.leave_reason}
                    </p>
                  )}
                </div>
              ) : (
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
                    <Badge tone="sage">
                      {availability?.slots.filter((s) => s.status === "available").length || 0} Slots Available
                    </Badge>

                    <span style={{ fontSize: "0.8125rem", color: "var(--color-slate)" }}>
                      Click any available slot to hold it for 5 minutes
                    </span>
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))",
                      gap: "0.5rem",
                    }}
                  >
                    {availability?.slots.map((slot) => {
                      const isAvailable = slot.status === "available";
                      return (
                        <button
                          key={slot.start_time}
                          disabled={!isAvailable || holdingSlot}
                          onClick={() => handleSlotClick(slot)}
                          style={{
                            padding: "0.625rem 0.5rem",
                            borderRadius: "var(--radius-control)",
                            textAlign: "center",
                            fontSize: "0.875rem",
                            fontFamily: "var(--font-mono)",
                            border: `1px solid ${isAvailable ? "var(--color-sage)" : "var(--color-border)"}`,
                            background: isAvailable ? "var(--color-sage-tint)" : "var(--color-paper)",
                            color: isAvailable ? "#3f5b44" : "var(--color-slate)",
                            cursor: isAvailable ? "pointer" : "not-allowed",
                            opacity: isAvailable ? 1 : 0.6,
                            transition: "all var(--motion-fade)",
                          }}
                        >
                          <strong>{slot.start_time}</strong>
                          <span style={{ display: "block", fontSize: "0.75rem" }}>
                            {isAvailable ? "Click to Hold" : "Taken"}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Slot Hold & Symptom Form Card */}
        {heldAppointment && selectedDoctor && (
          <Card className="card-elevated" style={{ borderColor: remainingSeconds < 60 ? "var(--color-coral)" : "var(--color-ink)" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
              <div>
                <h2>Slot Held: {heldAppointment.slot_start} – {heldAppointment.slot_end}</h2>
                <p style={{ fontSize: "0.875rem", color: "var(--color-slate)", margin: 0 }}>
                  Doctor: {selectedDoctor.full_name} | Date: {heldAppointment.appt_date}
                </p>
              </div>

              {/* IBM Plex Mono Live Countdown */}
              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "0.75rem", color: "var(--color-slate)", display: "block" }}>
                  Time remaining to confirm
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "1.5rem",
                    fontWeight: 700,
                    color: remainingSeconds < 60 ? "var(--color-coral)" : "var(--color-ink)",
                  }}
                >
                  {formatTime(remainingSeconds)}
                </span>
              </div>
            </div>

            {/* Depleting Progress Bar */}
            <div
              style={{
                width: "100%",
                height: "6px",
                background: "var(--color-paper)",
                borderRadius: "var(--radius-pill)",
                overflow: "hidden",
                margin: "1rem 0",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${(remainingSeconds / 300) * 100}%`,
                  background: remainingSeconds < 60 ? "var(--color-coral)" : "var(--color-sage)",
                  transition: "width 1s linear, background-color 0.3s ease",
                }}
              />
            </div>

            <form onSubmit={handleConfirmSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <TextArea
                label="Tell us what's going on (Symptoms / Reason for Visit)"
                placeholder="e.g. Chest pain for 2 days, mild fever..."
                value={symptomsText}
                onChange={(e) => setSymptomsText(e.target.value)}
                hint="Shared with the doctor before your consultation to generate a pre-visit summary."
              />

              <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => {
                    setHeldAppointment(null);
                    if (selectedDoctor) loadAvailability(selectedDoctor.id, selectedDate);
                  }}
                >
                  Release Slot
                </Button>
                <Button type="submit" variant="primary" disabled={confirming}>
                  {confirming ? "Confirming..." : "Confirm Appointment"}
                </Button>
              </div>
            </form>
          </Card>
        )}

        {/* APPOINTMENT SUMMARY MODAL (H5) */}
        {activeSummary && (
          <div className="modal-overlay">
            <div className="modal-dialog" style={{ maxWidth: "600px" }}>
              <div className="modal-header">
                <h2>Appointment Details & Summary</h2>
                <button type="button" onClick={() => setActiveSummary(null)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1.25rem" }}>
                  &times;
                </button>
              </div>

              <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
                <div>
                  <span style={{ fontSize: "0.75rem", color: "var(--color-slate)", textTransform: "uppercase", display: "block" }}>
                    Doctor Consultation
                  </span>
                  <strong style={{ fontSize: "1.125rem" }}>
                    Dr. {activeSummary.doctor_name} ({activeSummary.specialisation})
                  </strong>
                  <span style={{ display: "block", fontSize: "0.875rem", color: "var(--color-slate)", marginTop: "0.25rem" }}>
                    Date: {activeSummary.appt_date} | Time: {activeSummary.slot_start} – {activeSummary.slot_end}
                  </span>
                </div>

                <div>
                  <span style={{ fontSize: "0.75rem", color: "var(--color-slate)", textTransform: "uppercase", display: "block", marginBottom: "0.25rem" }}>
                    Status
                  </span>
                  <Badge tone={activeSummary.status === "completed" || activeSummary.status === "confirmed" ? "sage" : activeSummary.status === "held" ? "amber" : "coral"}>
                    {activeSummary.status.toUpperCase()}
                  </Badge>
                </div>

                {/* Pre-Visit Triage Summary */}
                {activeSummary.symptom_summary && (
                  <div style={{ background: "var(--color-paper)", padding: "1rem", borderRadius: "var(--radius-control)", border: "1px solid var(--color-border)" }}>
                    <h3 style={{ margin: 0, fontSize: "0.9375rem" }}>Pre-Visit Symptoms & Urgency</h3>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.5rem" }}>
                      <span style={{ fontSize: "0.8125rem", color: "var(--color-slate)" }}>AI Urgency:</span>
                      <UrgencyBadge level={activeSummary.symptom_summary.urgency || "Low"} />
                    </div>
                    <p style={{ margin: "0.5rem 0 0 0", fontSize: "0.9375rem" }}>
                      <strong>Chief Complaint:</strong> {activeSummary.symptom_summary.chief_complaint}
                    </p>
                    <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.875rem", color: "var(--color-slate)" }}>
                      <strong>Submitted Symptoms:</strong> {activeSummary.symptom_summary.raw_symptoms}
                    </p>
                  </div>
                )}

                {/* Post-Visit Care Summary */}
                {activeSummary.visit_note && (
                  <div style={{ background: "var(--color-sage-tint)", padding: "1rem", borderRadius: "var(--radius-control)", border: "1px solid var(--color-sage)" }}>
                    <h3 style={{ margin: 0, fontSize: "0.9375rem", color: "#3f5b44" }}>Doctor Care Summary</h3>
                    <p style={{ fontSize: "0.9375rem", marginTop: "0.5rem", margin: "0.5rem 0 0 0", color: "var(--color-ink)" }}>
                      {activeSummary.visit_note.patient_friendly_summary || activeSummary.visit_note.clinical_notes}
                    </p>

                    {activeSummary.visit_note.prescriptions.length > 0 && (
                      <div style={{ marginTop: "0.75rem" }}>
                        <span style={{ fontSize: "0.8125rem", color: "#3f5b44", fontWeight: 600, display: "block" }}>
                          Prescribed Medication Instructions:
                        </span>
                        <ul style={{ margin: "0.25rem 0 0 1.25rem", padding: 0, fontSize: "0.875rem", color: "var(--color-ink)" }}>
                          {activeSummary.visit_note.prescriptions.map((p, idx) => (
                            <li key={idx}>
                              <strong>{p.medication_name}</strong> ({p.dosage}) — {p.frequency} for {p.duration_days} days
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="modal-footer" style={{ marginTop: "1.5rem" }}>
                <Button variant="secondary" onClick={() => setActiveSummary(null)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
