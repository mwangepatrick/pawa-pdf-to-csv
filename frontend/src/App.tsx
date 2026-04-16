import { useState, useCallback, useEffect, useRef } from "react";
import "./App.css";
import UploadZone from "./components/UploadZone";
import Progress from "./components/Progress";
import Result from "./components/Result";
import { uploadPdf, pollStatus, StatusResponse } from "./api/client";

type AppState =
  | { step: "upload" }
  | { step: "processing"; jobId: string; filename: string; status: StatusResponse | null }
  | { step: "result"; jobId: string; data: StatusResponse }
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
          setState({ step: "result", jobId: state.jobId, data: status });
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

  return (
    <div className="app">
      <h1>PDF to CSV</h1>
      <p className="tagline">Extract tables from PDFs and convert them to CSV</p>

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
          downloadToken={state.data.download_token!}
          rowCount={state.data.row_count!}
          totalPages={state.data.total_pages!}
          jobId={state.jobId}
          onReset={handleReset}
        />
      )}

      {state.step === "error" && (
        <div style={{ textAlign: "center", padding: 48 }}>
          <p style={{ color: "#ef4444", fontSize: 18, marginBottom: 16 }}>
            {state.message}
          </p>
          {state.message.includes("No tables found") && state.file && (
            <button
              onClick={() => startUpload(state.file!, true)}
              style={{
                padding: "10px 24px",
                background: "#2563eb",
                color: "white",
                border: "none",
                borderRadius: 6,
                cursor: "pointer",
                marginBottom: 12,
              }}
            >
              Try Text Extraction Instead
            </button>
          )}
          <br />
          <button
            onClick={handleReset}
            style={{
              padding: "10px 24px",
              background: "transparent",
              color: "#888",
              border: "1px solid #444",
              borderRadius: 6,
              cursor: "pointer",
              marginTop: 8,
            }}
          >
            Upload a Different File
          </button>
        </div>
      )}
    </div>
  );
}
