import type { HTMLAttributes, ReactNode } from "react";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
  children: ReactNode;
}

/**
 * Base Card — Frontend Design Document §2.3 / §5.
 * 12px radius, no shadow by default — elevation is reserved for the
 * slot-hold countdown card and modal dialogs only (`elevated`).
 */
export function Card({ elevated = false, className, children, ...rest }: CardProps) {
  const classes = ["card", elevated && "card-elevated", className].filter(Boolean).join(" ");
  return (
    <div className={classes} {...rest}>
      {children}
    </div>
  );
}
