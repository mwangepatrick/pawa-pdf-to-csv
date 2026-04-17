import { useRef, useState } from "react";
import type { FormEvent } from "react";
import TurnstileWidget, { type TurnstileHandle } from "./TurnstileWidget";

type EmailState = "idle" | "sending" | "sent" | "error";

interface ResultProps {
  filename: string;
  rowCount: number;
  totalPages: number;
  jobId: string;
  onReset: () => void;
  emailState: EmailState;
  onSendEmail: (email: string, turnstileToken: string) => Promise<void>;
}

export default function Result({
  filename,
  rowCount,
  totalPages,
  jobId,
  onReset,
  emailState,
  onSendEmail,
}: ResultProps) {
  const [email, setEmail] = useState("");
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const widgetRef = useRef<TurnstileHandle>(null);

  const pageLabel = totalPages === 1 ? "1 page" : `${totalPages} pages`;
  const csvName = filename.replace(/\.pdf$/i, ".csv");
  const deliveryLabel =
    emailState === "sent"
      ? "Delivered"
      : emailState === "sending"
        ? "Sending..."
        : "Ready to email";

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setSubmitError("Enter an email address to continue.");
      return;
    }

    if (!turnstileToken) {
      setSubmitError("Complete the verification challenge before sending.");
      return;
    }

    setSubmitError(null);

    try {
      await onSendEmail(trimmedEmail, turnstileToken);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Email delivery failed.";
      setSubmitError(message);
      widgetRef.current?.reset();
      setTurnstileToken(null);
    }
  };

  return (
    <div className="result-card">
      <div className="result-status-row">
        <div className="result-badge">Conversion complete</div>
        <span className="result-status">{deliveryLabel}</span>
      </div>

      <h2>Your CSV is ready to email</h2>
      <p className="result-copy">
        {rowCount} rows extracted from {pageLabel} in {filename}. The browser stays on this page while the completed CSV is delivered by email.
      </p>

      <div className="result-stats" aria-label="Conversion summary">
        <article>
          <strong>{rowCount}</strong>
          <span>Rows extracted</span>
        </article>
        <article>
          <strong>{pageLabel}</strong>
          <span>Pages processed</span>
        </article>
        <article>
          <strong>{jobId}</strong>
          <span>Job reference</span>
        </article>
      </div>

      <form className="email-form" onSubmit={handleSubmit}>
        <label htmlFor="email-address">Send the CSV to</label>
        <div className="email-row">
          <input
            id="email-address"
            type="email"
            autoComplete="email"
            inputMode="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            disabled={emailState === "sending" || emailState === "sent"}
            aria-describedby="email-help"
          />
          <button
            type="submit"
            className="primary-button"
            disabled={emailState === "sending" || emailState === "sent"}
          >
            {emailState === "sending" ? "Sending..." : "Email my CSV"}
          </button>
        </div>

        <div id="email-help" className="result-help">
          <span>{csvName}</span>
          <span>Delivered by email, not a browser download.</span>
        </div>

        <TurnstileWidget
          ref={widgetRef}
          onTokenChange={(token) => {
            setTurnstileToken(token);
            if (token) {
              setSubmitError(null);
            }
          }}
        />

        {emailState === "sent" ? (
          <div className="success-message">
            Email sent. Check <strong>{email}</strong> for the CSV.
          </div>
        ) : null}

        {submitError ? <div className="error-message">{submitError}</div> : null}
      </form>

      <button type="button" className="secondary-button result-reset" onClick={onReset}>
        Upload another PDF
      </button>
    </div>
  );
}
