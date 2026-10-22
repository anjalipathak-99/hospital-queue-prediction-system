import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getQueueStatus, cancelAppointment } from "../api/api";
import { StatusBadge, LoadingSpinner } from "../components/Widgets";

const POLL_INTERVAL_MS = 10000;

export default function QueueStatus() {
  const { appointmentId } = useParams();
  const navigate = useNavigate();
  const [appointment, setAppointment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState("");

  const fetchStatus = useCallback(() => {
    getQueueStatus(appointmentId)
      .then((res) => {
        setAppointment(res.data);
        setError("");
      })
      .catch((err) => setError(err.response?.data?.error || "Could not load queue status."))
      .finally(() => setLoading(false));
  }, [appointmentId]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleCancel = async () => {
    if (!window.confirm("Cancel this appointment?")) return;
    setCancelling(true);
    try {
      await cancelAppointment(appointmentId);
      fetchStatus();
    } catch (err) {
      alert(err.response?.data?.error || "Could not cancel the appointment");
    } finally {
      setCancelling(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  if (!appointment) {
    return (
      <div className="container my-4" style={{ maxWidth: 560 }}>
        <div className="alert alert-danger">{error || "Appointment not found."}</div>
        <button className="btn btn-outline-secondary" onClick={() => navigate("/patient")}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  const isActive = ["waiting", "consulting"].includes(appointment.status);

  return (
    <div className="container my-4" style={{ maxWidth: 560 }}>
      <div className="card-panel text-center">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h4 className="mb-0">Live Queue Status</h4>
          <StatusBadge status={appointment.status} />
        </div>

        <p className="text-muted mb-1">
          {appointment.doctor_name} &middot; {appointment.department_name}
        </p>

        <div className="row my-4">
          <div className="col-4">
            <div className="queue-number-big">{appointment.queue_number}</div>
            <div className="text-muted small">Your Number</div>
          </div>
          <div className="col-4">
            <div className="queue-number-big">{appointment.patients_ahead ?? "-"}</div>
            <div className="text-muted small">Patients Ahead</div>
          </div>
          <div className="col-4">
            <div className="queue-number-big">{appointment.predicted_waiting_time ?? "-"}</div>
            <div className="text-muted small">Est. Minutes</div>
          </div>
        </div>

        {appointment.status === "waiting" && (
          <div className="alert alert-info">
            You are position <strong>#{appointment.queue_position}</strong> in the queue. This page
            refreshes automatically every 10 seconds.
          </div>
        )}
        {appointment.status === "consulting" && (
          <div className="alert alert-primary">You are currently being consulted.</div>
        )}
        {appointment.status === "completed" && (
          <div className="alert alert-success">Your consultation has been completed.</div>
        )}
        {["cancelled", "skipped", "absent"].includes(appointment.status) && (
          <div className="alert alert-secondary text-capitalize">
            This appointment was marked as {appointment.status}.
          </div>
        )}

        <div className="d-flex gap-2 justify-content-center mt-3">
          {isActive && appointment.status === "waiting" && (
            <button className="btn btn-outline-danger" onClick={handleCancel} disabled={cancelling}>
              {cancelling ? "Cancelling..." : "Cancel Appointment"}
            </button>
          )}
          <button className="btn btn-outline-secondary" onClick={() => navigate("/patient")}>
            Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
