export default function StatusBadge({ status }) {
  const isReady = status === "ready_to_save";
  return (
    <span
      className="status-badge"
      style={{
        background: isReady ? "var(--color-green-bg)" : "var(--color-amber-bg)",
        color: isReady ? "var(--color-green-text)" : "var(--color-amber-text)",
      }}
    >
      <span
        className="status-dot"
        style={{ background: isReady ? "var(--color-green-dot)" : "var(--color-amber-dot)" }}
      />
      {isReady ? "Ready to Save" : "Pending Triage"}
    </span>
  );
}
