export type VitalsLineTone = "ink" | "sage" | "amber" | "coral";

export interface VitalsLineProps {
  tone?: VitalsLineTone;
  /** One-shot draw-in animation — only on booking confirm / post-visit reveal (§2.5). */
  animate?: boolean;
  "aria-label"?: string;
}

/**
 * The signature vitals-line divider (Frontend Design Document §2.4) —
 * a flattened ECG-style pulse used as a section divider across all
 * three portals. Drawn once as SVG here, colored via the current
 * status tone. Decorative by default (aria-hidden) unless a label is
 * supplied.
 */
export function VitalsLine({ tone = "ink", animate = false, ...rest }: VitalsLineProps) {
  const classes = ["vitals-line", tone !== "ink" && `vitals-line-${tone}`, animate && "vitals-line-animate"]
    .filter(Boolean)
    .join(" ");

  return (
    <svg
      viewBox="0 0 240 24"
      className={classes}
      role={rest["aria-label"] ? "img" : undefined}
      aria-hidden={rest["aria-label"] ? undefined : true}
      aria-label={rest["aria-label"]}
    >
      <path
        d="M0 12 H80 L92 4 L104 20 L116 2 L128 22 L140 12 H240"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      />
    </svg>
  );
}
