import { forwardRef, useId, type InputHTMLAttributes } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

/**
 * Base Input — Frontend Design Document §5 / Chunk 4.
 * Wraps a labeled field with an optional hint and error message.
 * Error state drives `data-invalid`, styled via globals.css rather
 * than color alone so it stays readable without relying on hue (§7).
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, hint, error, id, className, ...rest },
  ref
) {
  const generatedId = useId();
  const inputId = id || generatedId;

  return (
    <div className="field">
      {label && (
        <label className="field-label" htmlFor={inputId}>
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        className={["input", className].filter(Boolean).join(" ")}
        data-invalid={Boolean(error)}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
        {...rest}
      />
      {error ? (
        <p className="field-error" id={`${inputId}-error`} role="alert">
          {error}
        </p>
      ) : hint ? (
        <p className="field-hint" id={`${inputId}-hint`}>
          {hint}
        </p>
      ) : null}
    </div>
  );
});
