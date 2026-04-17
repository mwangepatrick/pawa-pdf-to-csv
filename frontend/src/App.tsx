import { useState, useCallback, useEffect, useRef } from "react";
import "./App.css";
import UploadZone from "./components/UploadZone";
import Progress from "./components/Progress";
import Result from "./components/Result";
import { uploadPdf, pollStatus, sendEmail } from "./api/client";
import type { StatusResponse } from "./api/client";

type EmailState = "idle" | "sending" | "sent" | "error";

type AppState =
  | { step: "upload" }
  | { step: "processing"; jobId: string; filename: string; status: StatusResponse | null }
  | { step: "result"; jobId: string; data: StatusResponse; emailState: EmailState }
  | { step: "error"; message: string; file?: File };

export default function App() {
  const [state, setState] = useState<AppState>({ step: "upload" });
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastFileRef = useRef<File | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startUpload = useCallback(async (file: File, textFallback = false) => {
    try {
      lastFileRef.current = file;
      setState({ step: "processing", jobId: "", filename: file.name, status: null });
      const res = await uploadPdf(file, textFallback);
      setState({ step: "processing", jobId: res.job_id, filename: file.name, status: null });
    } catch (err) {
      setState({
        step: "error",
        message: err instanceof Error ? err.message : "Upload failed",
        file,
      });
    }
  }, []);

  const handleFileSelected = useCallback((file: File) => {
    startUpload(file);
  }, [startUpload]);

  // Poll for status when in processing state
  useEffect(() => {
    if (state.step !== "processing" || !state.jobId) return;

    const poll = async () => {
      try {
        const status = await pollStatus(state.jobId);
        if (status.status === "completed") {
          stopPolling();
          setState({ step: "result", jobId: state.jobId, data: status, emailState: "idle" });
        } else if (status.status === "failed") {
          stopPolling();
          setState({ step: "error", message: status.error || "Conversion failed", file: lastFileRef.current ?? undefined });
        } else {
          setState((prev) =>
            prev.step === "processing"
              ? { ...prev, status }
              : prev
          );
        }
      } catch {
        stopPolling();
        setState({ step: "error", message: "Lost connection to server" });
      }
    };

    poll(); // immediate first poll
    pollRef.current = setInterval(poll, 1500);
    return stopPolling;
  }, [state.step, state.step === "processing" ? state.jobId : null, stopPolling]);

  const handleReset = useCallback(() => {
    stopPolling();
    setState({ step: "upload" });
  }, [stopPolling]);

  const activeJobId = state.step === "result" ? state.jobId : null;

  const handleSendEmail = useCallback(
    async (email: string, turnstileToken: string) => {
      if (!activeJobId) {
        throw new Error("No completed job is available for email delivery.");
      }

      setState((prev) =>
        prev.step === "result" ? { ...prev, emailState: "sending" } : prev
      );

      try {
        await sendEmail(activeJobId, email, turnstileToken);
        setState((prev) =>
          prev.step === "result" ? { ...prev, emailState: "sent" } : prev
        );
      } catch (err) {
        setState((prev) =>
          prev.step === "result" ? { ...prev, emailState: "error" } : prev
        );
        throw err;
      }
    },
    [activeJobId]
  );

  return (
    <div className="app-shell">
      <main className="app-layout">
        <section className="hero-panel">
          <p className="hero-kicker">PDF to CSV</p>
          <h1 className="hero-title">PDF to CSV</h1>
          <p className="hero-copy">
            Upload a PDF, let the extractor do the work, and get the finished CSV delivered by email.
          </p>

          <div className="hero-step-grid" aria-label="How it works">
            <article className="hero-step">
              <span className="hero-step-index">1</span>
              <p className="hero-step-title">Upload the PDF</p>
              <p className="hero-step-copy">Drop in a file up to 20MB and start the conversion.</p>
            </article>
            <article className="hero-step">
              <span className="hero-step-index">2</span>
              <p className="hero-step-title">We extract the tables</p>
              <p className="hero-step-copy">Progress updates stay on one page while the job runs.</p>
            </article>
            <article className="hero-step">
              <span className="hero-step-index">3</span>
              <p className="hero-step-title">Delivered by email</p>
              <p className="hero-step-copy">No download hunt. The completed CSV lands in your inbox.</p>
            </article>
          </div>

          <p className="hero-note">Everything finishes here, but the file arrives in email.</p>
        </section>

        <section className="workspace-panel" aria-live="polite">
          {state.step === "upload" && (
            <UploadZone onFileSelected={handleFileSelected} />
          )}

          {state.step === "processing" && (
            <Progress
              filename={state.filename}
              pagesProcessed={state.status?.pages_processed ?? null}
              totalPages={state.status?.total_pages ?? null}
            />
          )}

          {state.step === "result" && (
            <Result
              filename={state.data.filename}
              rowCount={state.data.row_count ?? 0}
              totalPages={state.data.total_pages ?? 0}
              jobId={state.jobId}
              emailState={state.emailState}
              onReset={handleReset}
              onSendEmail={handleSendEmail}
            />
          )}

          {state.step === "error" && (
            <div className="error-panel">
              <div className="error-badge">Conversion stopped</div>
              <h2>{state.message}</h2>
              <p>
                Try another PDF or rerun the same file with text extraction if the document is text-heavy.
              </p>
              {state.message.includes("No tables found") && state.file && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => startUpload(state.file!, true)}
                >
                  Try text extraction instead
                </button>
              )}
              <button type="button" className="primary-button" onClick={handleReset}>
                Upload a different file
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
