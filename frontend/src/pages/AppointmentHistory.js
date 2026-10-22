import React, { useEffect, useState } from "react";
import { getMyAppointments } from "../api/api";
import { StatusBadge, LoadingSpinner, EmptyState } from "../components/Widgets";

export default function AppointmentHistory() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    setLoading(true);
    getMyAppointments(filter || undefined)
      .then((res) => setAppointments(res.data))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div className="container my-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h3>Appointment History</h3>
        <select className="form-select" style={{ width: 200 }} value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="waiting">Waiting</option>
          <option value="consulting">Consulting</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
          <option value="skipped">Skipped</option>
          <option value="absent">Absent</option>
        </select>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : appointments.length === 0 ? (
        <EmptyState message="No appointments found." />
      ) : (
        <div className="card-panel p-0">
          <table className="table mb-0">
            <thead>
              <tr>
                <th>Queue No.</th>
                <th>Doctor</th>
                <th>Department</th>
                <th>Type</th>
                <th>Date</th>
                <th>Predicted Wait</th>
                <th>Actual Wait</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((a) => (
                <tr key={a.id}>
                  <td>{a.queue_number}</td>
                  <td>{a.doctor_name}</td>
                  <td>{a.department_name}</td>
                  <td className="text-capitalize">{a.appointment_type?.replace("_", " ")}</td>
                  <td>{a.created_at ? new Date(a.created_at).toLocaleString() : "-"}</td>
                  <td>{a.predicted_waiting_time ? `${a.predicted_waiting_time} min` : "-"}</td>
                  <td>{a.actual_waiting_time ? `${a.actual_waiting_time} min` : "-"}</td>
                  <td><StatusBadge status={a.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
