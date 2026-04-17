import { useState } from "react";
import type { FormEvent } from "react";
import { getDownloadUrl, sendEmail } from "../api/client";

interface ResultProps {
  filename: string;
  downloadToken: string;
  rowCount: number;
  totalPages: number;
  jobId: string;
  onReset: () => void;
}

export default function Result({
  filename,
  downloadToken,
  rowCount,
  totalPages,
  jobId,
  onReset,
}: ResultProps) {
  const [email, setEmail] = useState("");
  const [emailStatus, setEmailStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [emailError, setEmailError] = useState<string | null>(null);

  const csvName = filename.replace(/\.pdf$/i, ".csv");
  const downloadUrl = getDownloadUrl(downloadToken);

  const handleEmailSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setEmailStatus("sending");
    setEmailError(null);
    try {
      await sendEmail(jobId, email.trim());
      setEmailStatus("sent");
    } catch (err) {
      setEmailStatus("error");
      setEmailError(err instanceof Error ? err.message : "Failed to send email");
    }
  };

  return (
    <div style={{ textAlign: "center", padding: 48 }}>
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: "50%",
          background: "#22c55e",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 24px",
          fontSize: 24,
          color: "white",
        }}
      >
        ✓
      </div>

      <h2 style={{ marginBottom: 8 }}>Conversion Complete</h2>
      <p style={{ color: "#888", marginBottom: 24 }}>
        {rowCount} rows extracted from {totalPages} page{totalPages !== 1 ? "s" : ""}
      </p>

      <a
        href={downloadUrl}
        download={csvName}
        style={{
          display: "inline-block",
          padding: "12px 32px",
          background: "#2563eb",
          color: "white",
          borderRadius: 6,
          textDecoration: "none",
          fontSize: 16,
          marginBottom: 32,
        }}
      >
        Download {csvName}
      </a>

      <div
        style={{
          maxWidth: 400,
          margin: "0 auto",
          padding: 24,
          background: "#111",
          borderRadius: 8,
          border: "1px solid #333",
        }}
      >
        <p style={{ marginBottom: 12, fontSize: 14 }}>
          Or send the download link to your email
        </p>

        {emailStatus === "sent" ? (
          <p style={{ color: "#22c55e" }}>
            Email sent! Link expires in 24 hours.
          </p>
        ) : (
          <form onSubmit={handleEmailSubmit} style={{ display: "flex", gap: 8 }}>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={emailStatus === "sending"}
              style={{
                flex: 1,
                padding: "8px 12px",
                borderRadius: 6,
                border: "1px solid #444",
                background: "#1a1a1a",
                color: "white",
                fontSize: 14,
              }}
            />
            <button
              type="submit"
              disabled={emailStatus === "sending"}
              style={{
                padding: "8px 16px",
                background: emailStatus === "sending" ? "#555" : "#2563eb",
                color: "white",
                border: "none",
                borderRadius: 6,
                cursor: emailStatus === "sending" ? "not-allowed" : "pointer",
                fontSize: 14,
              }}
            >
              {emailStatus === "sending" ? "Sending..." : "Send"}
            </button>
          </form>
        )}
        {emailError && (
          <p style={{ color: "#ef4444", fontSize: 13, marginTop: 8 }}>{emailError}</p>
        )}
      </div>

      <button
        onClick={onReset}
        style={{
          marginTop: 32,
          padding: "8px 20px",
          background: "transparent",
          color: "#888",
          border: "1px solid #444",
          borderRadius: 6,
          cursor: "pointer",
          fontSize: 14,
        }}
      >
        Convert another PDF
      </button>
    </div>
  );
}
