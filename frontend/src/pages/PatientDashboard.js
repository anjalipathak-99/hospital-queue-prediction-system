import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyAppointments } from "../api/api";
import { StatusBadge, LoadingSpinner, EmptyState } from "../components/Widgets";

export default function PatientDashboard() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyAppointments()
      .then((res) => setAppointments(res.data))
      .finally(() => setLoading(false));
  }, []);

  const active = appointments.filter((a) => ["waiting", "consulting"].includes(a.status));
  const past = appointments.filter((a) => !["waiting", "consulting"].includes(a.status));

  return (
    <div className="container my-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h3>My Dashboard</h3>
        <Link to="/doctors" className="btn btn-primary-hospital">
          + Book New Appointment
        </Link>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          <h5 className="mb-3">Active Appointments</h5>
          {active.length === 0 ? (
            <EmptyState message="You have no active appointments right now." />
          ) : (
            <div className="row g-3 mb-4">
              {active.map((a) => (
                <div className="col-md-6" key={a.id}>
                  <div className="card-panel">
                    <div className="d-flex justify-content-between align-items-start">
                      <div>
                        <h5 className="mb-1">{a.doctor_name}</h5>
                        <div className="text-muted small">{a.department_name}</div>
                      </div>
                      <StatusBadge status={a.status} />
                    </div>
                    <div className="row mt-3 text-center">
                      <div className="col">
                        <div className="queue-number-big">{a.queue_number}</div>
                        <div className="text-muted small">Queue No.</div>
                      </div>
                      <div className="col">
                        <div className="fs-4 fw-bold">{a.predicted_waiting_time ?? "-"}</div>
                        <div className="text-muted small">Est. Wait (min)</div>
                      </div>
                    </div>
                    <Link to={`/queue/${a.id}`} className="btn btn-outline-secondary w-100 mt-3">
                      View Live Queue Status
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}

          <h5 className="mb-3">Recent History</h5>
          {past.length === 0 ? (
            <EmptyState message="No past appointments yet." />
          ) : (
            <div className="card-panel p-0">
              <table className="table mb-0">
                <thead>
                  <tr>
                    <th>Doctor</th>
                    <th>Department</th>
                    <th>Date</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {past.slice(0, 5).map((a) => (
                    <tr key={a.id}>
                      <td>{a.doctor_name}</td>
                      <td>{a.department_name}</td>
                      <td>{a.created_at ? new Date(a.created_at).toLocaleDateString() : "-"}</td>
                      <td><StatusBadge status={a.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="text-end mt-2">
            <Link to="/history">View full history &rarr;</Link>
          </div>
        </>
      )}
    </div>
  );
}
