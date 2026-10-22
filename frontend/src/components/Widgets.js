import React from "react";

export function StatCard({ label, value, icon }) {
  return (
    <div className="stat-card">
      <div className="d-flex justify-content-between align-items-start">
        <div>
          <div className="stat-label">{label}</div>
          <div className="stat-value">{value}</div>
        </div>
        {icon && <div style={{ fontSize: "1.75rem" }}>{icon}</div>}
      </div>
    </div>
  );
}

export function StatusBadge({ status }) {
  return <span className={`badge badge-${status} text-white text-capitalize`}>{status}</span>;
}

export function EmptyState({ message }) {
  return (
    <div className="text-center text-muted py-5">
      <div style={{ fontSize: "2rem" }}>📋</div>
      <p>{message}</p>
    </div>
  );
}

export function LoadingSpinner() {
  return (
    <div className="d-flex justify-content-center py-5">
      <div className="spinner-border" style={{ color: "#0f7a6e" }} role="status" />
    </div>
  );
}
