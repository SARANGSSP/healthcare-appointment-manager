import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "destructive";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
}

const sizeClass: Record<ButtonSize, string> = {
  sm: "btn-sm",
  md: "",
  lg: "btn-lg",
};

/**
 * Base Button — Frontend Design Document §5 / Chunk 4.
 * Buttons name the action a person takes, not the system operation
 * ("Confirm appointment", not "Submit") — see §6, enforced by callers.
 * `destructive` is the only variant allowed to use coral (§2.1: coral
 * never appears on a primary "Book" button).
 */
export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...rest
}: ButtonProps) {
  const classes = ["btn", `btn-${variant}`, sizeClass[size], className]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={classes} {...rest}>
      {children}
    </button>
  );
}
