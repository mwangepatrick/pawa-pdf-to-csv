import { useCallback, useState } from "react";
import type { DragEvent, ChangeEvent } from "react";

interface UploadZoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

const MAX_SIZE_MB = 20;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export default function UploadZone({ onFileSelected, disabled }: UploadZoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = useCallback((file: File): string | null => {
    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
      return "Please select a PDF file.";
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `File exceeds ${MAX_SIZE_MB}MB limit.`;
    }
    return null;
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      const err = validate(file);
      if (err) {
        setError(err);
        return;
      }
      setError(null);
      onFileSelected(file);
    },
    [validate, onFileSelected]
  );

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const onDragLeave = useCallback(() => setDragOver(false), []);

  const onChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      style={{
        border: `2px dashed ${dragOver ? "#2563eb" : "#555"}`,
        borderRadius: 12,
        padding: 48,
        textAlign: "center",
        background: dragOver ? "rgba(37, 99, 235, 0.05)" : "transparent",
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "all 0.2s",
      }}
    >
      <p style={{ fontSize: 18, marginBottom: 8 }}>
        Drag & drop a PDF here
      </p>
      <p style={{ color: "#888", marginBottom: 16 }}>or</p>
      <label
        style={{
          display: "inline-block",
          padding: "10px 24px",
          background: "#2563eb",
          color: "white",
          borderRadius: 6,
          cursor: disabled ? "not-allowed" : "pointer",
        }}
      >
        Browse Files
        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={onChange}
          disabled={disabled}
          style={{ display: "none" }}
        />
      </label>
      <p style={{ color: "#888", fontSize: 13, marginTop: 12 }}>
        PDF files up to {MAX_SIZE_MB}MB
      </p>
      {error && (
        <p style={{ color: "#ef4444", marginTop: 12 }}>{error}</p>
      )}
    </div>
  );
}
