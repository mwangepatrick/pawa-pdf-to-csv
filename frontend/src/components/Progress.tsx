interface ProgressProps {
  filename: string;
  pagesProcessed: number | null;
  totalPages: number | null;
}

export default function Progress({ filename, pagesProcessed, totalPages }: ProgressProps) {
  const hasPageInfo = totalPages !== null && totalPages > 0;
  const currentPages = pagesProcessed ?? 0;
  const progress = hasPageInfo ? Math.min(100, Math.round((currentPages / totalPages) * 100)) : null;
  const pageLabel = hasPageInfo ? `${currentPages}/${totalPages}` : "processing";

  return (
    <div className="progress-card">
      <div className="progress-orb" aria-hidden="true" />
      <div className="progress-copy">Converting {filename}</div>
      <p className="progress-message">The extractor is preparing the CSV. The finished file will be delivered by email.</p>

      {hasPageInfo ? (
        <>
          <div className="progress-status">
            <span>Pages processed</span>
            <strong>{pageLabel}</strong>
          </div>
          <div className="progress-track" aria-label="Conversion progress">
            <div className="progress-bar" style={{ width: `${progress}%` }} />
          </div>
        </>
      ) : (
        <div className="progress-status">
          <span>Status</span>
          <strong>Processing</strong>
        </div>
      )}
    </div>
  );
}
