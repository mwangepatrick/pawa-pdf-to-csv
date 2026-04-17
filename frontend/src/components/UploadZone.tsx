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
      const validationError = validate(file);
      if (validationError) {
        setError(validationError);
        return;
      }

      setError(null);
      onFileSelected(file);
    },
    [validate, onFileSelected]
  );

  const onDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault();
      setDragOver(false);
      const file = event.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    setDragOver(true);
  }, []);

  const onDragLeave = useCallback(() => setDragOver(false), []);

  const onChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        handleFile(file);
      }
    },
    [handleFile]
  );

  return (
    <div className={`upload-zone ${dragOver ? "upload-zone--active" : ""}`} onDrop={onDrop} onDragOver={onDragOver} onDragLeave={onDragLeave}>
      <div className="upload-zone__eyebrow">Start here</div>
      <p className="upload-zone__title">Drop a PDF to begin the conversion</p>
      <p className="upload-zone__copy">We extract the table data and deliver the CSV by email once it is ready.</p>

      <label className="primary-button upload-zone__button">
        Browse PDFs
        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={onChange}
          disabled={disabled}
          style={{ display: "none" }}
        />
      </label>

      <p className="upload-zone__meta">PDF files up to {MAX_SIZE_MB}MB</p>

      {error ? <p className="upload-zone__error">{error}</p> : null}
    </div>
  );
}
