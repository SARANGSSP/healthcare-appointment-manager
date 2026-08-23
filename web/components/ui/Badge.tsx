import type { ReactNode } from "react";

export type BadgeTone = "sage" | "amber" | "coral" | "ink";

export interface BadgeProps {
  tone: BadgeTone;
  icon?: ReactNode;
  children: ReactNode;
}

const DEFAULT_ICON: Record<BadgeTone, string> = {
  sage: "●",
  amber: "▲",
  coral: "■",
  ink: "○",
};

/**
 * Urgency + status Badge — Frontend Design Document §2.1 / §5.
 * Pill shape, sage/amber/coral carry real clinical-signal meaning
 * (Low/Medium/High urgency, confirmed/pending/cancelled status).
 * Always renders an icon + text alongside color — never color alone
 * (§7 accessibility).
 */
export function Badge({ tone, icon, children }: BadgeProps) {
  return (
    <span className={`badge badge-${tone}`}>
      <span className="badge-icon" aria-hidden="true">
        {icon ?? DEFAULT_ICON[tone]}
      </span>
      {children}
    </span>
  );
}

/** Convenience wrapper for the Low/Medium/High urgency triage output. */
export function UrgencyBadge({ level }: { level: "Low" | "Medium" | "High" }) {
  const tone: BadgeTone = level === "Low" ? "sage" : level === "Medium" ? "amber" : "coral";
  return <Badge tone={tone}>{level}</Badge>;
}

/** Convenience wrapper for appointment/job status pills. */
export function StatusBadge({
  status,
}: {
  status: "confirmed" | "pending" | "cancelled" | "held" | "completed" | "failed";
}) {
  const toneByStatus: Record<typeof status, BadgeTone> = {
    confirmed: "sage",
    completed: "sage",
    pending: "amber",
    held: "amber",
    cancelled: "coral",
    failed: "coral",
  };
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  return <Badge tone={toneByStatus[status]}>{label}</Badge>;
}
