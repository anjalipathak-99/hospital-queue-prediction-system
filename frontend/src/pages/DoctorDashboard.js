import React, { useEffect, useState, useCallback } from "react";
import {
  getDoctorQueue,
  getDoctorStats,
  startConsultation,
  completeConsultation,
  skipPatient,
  markAbsent,
  setDoctorAvailability,
} from "../api/api";
import { StatCard, StatusBadge, LoadingSpinner, EmptyState } from "../components/Widgets";

const POLL_INTERVAL_MS = 8000;

export default function DoctorDashboard() {
  const [queue, setQueue] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState(null);
  const [available, setAvailable] = useState(true);

  const load = useCallback(() => {
    Promise.all([getDoctorQueue(), getDoctorStats()])
      .then(([q, s]) => {
        setQueue(q.data);
        setStats(s.data);
        if (typeof s.data.is_available === "boolean") setAvailable(s.data.is_available);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [load]);

  const runAction = async (id, fn) => {
    setActioningId(id);
    try {
      await fn(id);
      load();
    } catch (err) {
      alert(err.response?.data?.error || "Action failed");
    } finally {
      setActioningId(null);
    }
  };

  const toggleAvailability = async () => {
    const next = !available;
    setAvailable(next);
    try {
      await setDoctorAvailability(next);
      load();
    } catch (err) {
      setAvailable(!next);
      alert(err.response?.data?.error || "Could not update availability");
    }
  };

  if (loading) return <LoadingSpinner />;

  const consulting = queue.find((a) => a.status === "consulting");
  const waiting = queue.filter((a) => a.status === "waiting");

  return (
    <div className="container my-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h3>Doctor Dashboard</h3>
        <div className="form-check form-switch">
          <input
            className="form-check-input"
            type="checkbox"
            checked={available}
            onChange={toggleAvailability}
            id="availSwitch"
          />
          <label className="form-check-label" htmlFor="availSwitch">
            {available ? "Available" : "Unavailable"}
          </label>
        </div>
      </div>

      {stats && (
        <div className="row g-3 mb-4">
          <div className="col-6 col-md-3">
            <StatCard label="Today's Total" value={stats.total_today} icon="📋" />
          </div>
          <div className="col-6 col-md-3">
            <StatCard label="Waiting" value={stats.waiting} icon="⏳" />
          </div>
          <div className="col-6 col-md-3">
            <StatCard label="Completed" value={stats.completed} icon="✅" />
          </div>
          <div className="col-6 col-md-3">
            <StatCard label="Avg. Wait (min)" value={stats.average_wait_minutes} icon="⏱️" />
          </div>
        </div>
      )}

      <h5 className="mb-3">Currently Consulting</h5>
      {!consulting ? (
        <EmptyState message="No patient is currently being consulted." />
      ) : (
        <div className="card-panel mb-4 border-start border-4" style={{ borderColor: "#2f8fd6" }}>
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-1">
                #{consulting.queue_number} &mdash; {consulting.patient_name}
              </h5>
              <span className="text-muted small text-capitalize">
                {consulting.appointment_type?.replace("_", " ")} &middot; Priority {consulting.priority_level}
              </span>
            </div>
            <button
              className="btn btn-primary-hospital"
              disabled={actioningId === consulting.id}
              onClick={() => runAction(consulting.id, completeConsultation)}
            >
              {actioningId === consulting.id ? "Completing..." : "Complete Consultation"}
            </button>
          </div>
        </div>
      )}

      <h5 className="mb-3">Waiting Queue ({waiting.length})</h5>
      {waiting.length === 0 ? (
        <EmptyState message="No patients waiting." />
      ) : (
        <div className="card-panel p-0">
          <table className="table mb-0 align-middle">
            <thead>
              <tr>
                <th>Queue No.</th>
                <th>Patient</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Est. Wait</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {waiting.map((a) => (
                <tr key={a.id}>
                  <td className="fw-bold">{a.queue_number}</td>
                  <td>{a.patient_name}</td>
                  <td className="text-capitalize">{a.appointment_type?.replace("_", " ")}</td>
                  <td>{a.priority_level}</td>
                  <td>{a.predicted_waiting_time ? `${a.predicted_waiting_time} min` : "-"}</td>
                  <td><StatusBadge status={a.status} /></td>
                  <td>
                    <div className="d-flex gap-1">
                      <button
                        className="btn btn-sm btn-primary-hospital"
                        disabled={!!consulting || actioningId === a.id}
                        onClick={() => runAction(a.id, startConsultation)}
                      >
                        Start
                      </button>
                      <button
                        className="btn btn-sm btn-outline-secondary"
                        disabled={actioningId === a.id}
                        onClick={() => runAction(a.id, skipPatient)}
                      >
                        Skip
                      </button>
                      <button
                        className="btn btn-sm btn-outline-danger"
                        disabled={actioningId === a.id}
                        onClick={() => runAction(a.id, markAbsent)}
                      >
                        Absent
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
