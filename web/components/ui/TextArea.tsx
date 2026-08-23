import { forwardRef, useId, type TextareaHTMLAttributes } from "react";

export interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
}

/**
 * Base TextArea — Frontend Design Document §5 / Chunk 4.
 * Same labeled-field pattern as Input; used for the symptom form
 * (Chunk 8) and clinical notes (Chunk 13).
 */
export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(function TextArea(
  { label, hint, error, id, className, ...rest },
  ref
) {
  const generatedId = useId();
  const textareaId = id || generatedId;

  return (
    <div className="field">
      {label && (
        <label className="field-label" htmlFor={textareaId}>
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        id={textareaId}
        className={["textarea", className].filter(Boolean).join(" ")}
        data-invalid={Boolean(error)}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${textareaId}-error` : hint ? `${textareaId}-hint` : undefined}
        {...rest}
      />
      {error ? (
        <p className="field-error" id={`${textareaId}-error`} role="alert">
          {error}
        </p>
      ) : hint ? (
        <p className="field-hint" id={`${textareaId}-hint`}>
          {hint}
        </p>
      ) : null}
    </div>
  );
});
