interface ProgressProps {
  filename: string;
  pagesProcessed: number | null;
  totalPages: number | null;
}

export default function Progress({ filename, pagesProcessed, totalPages }: ProgressProps) {
  const hasPageInfo = totalPages !== null && totalPages > 0;
  const pct = hasPageInfo && pagesProcessed !== null
    ? Math.round((pagesProcessed / totalPages) * 100)
    : null;

  return (
    <div style={{ textAlign: "center", padding: 48 }}>
      <div
        style={{
          width: 48,
          height: 48,
          border: "4px solid #333",
          borderTop: "4px solid #2563eb",
          borderRadius: "50%",
          animation: "spin 1s linear infinite",
          margin: "0 auto 24px",
        }}
      />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <p style={{ fontSize: 18, marginBottom: 8 }}>Converting {filename}...</p>
      {hasPageInfo ? (
        <>
          <p style={{ color: "#888" }}>
            Extracting tables from page {pagesProcessed ?? 0}/{totalPages}
          </p>
          <div
            style={{
              width: "100%",
              maxWidth: 300,
              height: 6,
              background: "#333",
              borderRadius: 3,
              margin: "16px auto 0",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${pct}%`,
                height: "100%",
                background: "#2563eb",
                borderRadius: 3,
                transition: "width 0.3s",
              }}
            />
          </div>
        </>
      ) : (
        <p style={{ color: "#888" }}>Processing...</p>
      )}
    </div>
  );
}
