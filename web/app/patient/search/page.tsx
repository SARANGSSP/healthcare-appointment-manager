"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "../../../components/shell/AppShell";
import { Badge } from "../../../components/ui/Badge";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { Input } from "../../../components/ui/Input";
import { Toast, type ToastVariant } from "../../../components/ui/Toast";
import { VitalsLine } from "../../../components/ui/VitalsLine";
import {
  clearSession,
  fetchDoctorAvailability,
  fetchDoctors,
  holdSlot,
  type Doctor,
  type DoctorAvailability,
  type TimeSlot,
} from "../../../lib/api";
import { useRequireRole } from "../../../lib/useRequireRole";

export default function PatientSearchPage() {
  const ready = useRequireRole("patient");
  const router = useRouter();

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loadingDoctors, setLoadingDoctors] = useState(true);
  const [specialisationFilter, setSpecialisationFilter] = useState("");
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [availability, setAvailability] = useState<DoctorAvailability | null>(null);
  const [loadingAvailability, setLoadingAvailability] = useState(false);
  const [holdingSlot, setHoldingSlot] = useState(false);

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

  useEffect(() => {
    if (ready) {
      loadDoctors();
    }
  }, [ready, loadDoctors]);

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
    loadAvailability(doc.id, selectedDate);
  };

  const handleDateChange = (newDate: string) => {
    setSelectedDate(newDate);
    if (selectedDoctor) {
      loadAvailability(selectedDoctor.id, newDate);
    }
  };

  const handleSlotClick = async (slot: TimeSlot) => {
    if (!selectedDoctor || slot.status !== "available" || holdingSlot) return;

    try {
      setHoldingSlot(true);
      await holdSlot({
        doctor_id: selectedDoctor.id,
        appt_date: selectedDate,
        slot_start: slot.start_time,
        slot_end: slot.end_time,
      });
      showToast("info", "Slot held", `Slot ${slot.start_time}–${slot.end_time} is held for 5 minutes.`);
      router.push("/patient");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Slot no longer available";
      showToast("failed", "Slot unavailable", msg);
      if (selectedDoctor) loadAvailability(selectedDoctor.id, selectedDate);
    } finally {
      setHoldingSlot(false);
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
          <h1>Doctor Search & Availability</h1>
          <p style={{ color: "var(--color-slate)", margin: 0 }}>
            Search doctors by specialisation and inspect real-time schedule availability.
          </p>
        </div>

        <VitalsLine tone="sage" animate />

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

        {selectedDoctor && (
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
      </div>
    </AppShell>
  );
}
