export interface UploadResponse {
  job_id: string;
  status: string;
}

export interface StatusResponse {
  job_id: string;
  status: "processing" | "completed" | "failed";
  filename: string;
  total_pages: number | null;
  pages_processed: number | null;
  download_token?: string;
  row_count?: number;
  error?: string;
}

export interface EmailResponse {
  sent: boolean;
}

const API_BASE = "/api";

export async function uploadPdf(file: File, textFallback = false): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const url = textFallback ? `${API_BASE}/upload?text_fallback=true` : `${API_BASE}/upload`;
  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function pollStatus(jobId: string): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/status/${jobId}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Status check failed");
  }
  return res.json();
}

export function getDownloadUrl(token: string): string {
  return `${API_BASE}/download/${token}`;
}

export async function sendEmail(jobId: string, email: string): Promise<EmailResponse> {
  const res = await fetch(`${API_BASE}/email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId, email }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Email send failed");
  }
  return res.json();
}
