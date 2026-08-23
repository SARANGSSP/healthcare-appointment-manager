import type { ReactNode } from "react";

export type ToastVariant = "success" | "failed" | "info";

export interface ToastProps {
  variant: ToastVariant;
  title: string;
  children?: ReactNode;
}

const ICON: Record<ToastVariant, string> = {
  success: "✓",
  failed: "✕",
  info: "ℹ",
};

/**
 * Status Toast — Frontend Design Document §5.
 * States: Success (sage) / Failed (coral) / Info (ink). Used for
 * booking confirm and notification failures surfaced to admin.
 * Failure copy explains what happened and what to do (§6), never a
 * raw error code on the patient side — enforced by callers.
 */
export function Toast({ variant, title, children }: ToastProps) {
  return (
    <div className={`toast toast-${variant}`} role={variant === "failed" ? "alert" : "status"}>
      <span aria-hidden="true">{ICON[variant]}</span>
      <div>
        <p className="toast-title">{title}</p>
        {children && <p className="toast-body">{children}</p>}
      </div>
    </div>
  );
}
