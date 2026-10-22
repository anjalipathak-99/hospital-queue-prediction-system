import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  adminStatsOverview,
  adminListDoctors,
  adminListDepartments,
  adminAddDoctor,
  adminEditDoctor,
  adminDeleteDoctor,
  adminCreateDepartment,
  adminMonitorQueues,
} from "../api/api";
import { StatCard, StatusBadge, LoadingSpinner, EmptyState } from "../components/Widgets";

const emptyDoctorForm = {
  full_name: "",
  email: "",
  password: "",
  department_id: "",
  specialization: "",
  average_consultation_time: 15,
};

export default function AdminDashboard() {
  const [overview, setOverview] = useState(null);
  const [doctors, setDoctors] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [queues, setQueues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [doctorForm, setDoctorForm] = useState(emptyDoctorForm);
  const [editingId, setEditingId] = useState(null);
  const [newDeptName, setNewDeptName] = useState("");
  const [error, setError] = useState("");

  const loadAll = useCallback(() => {
    Promise.all([
      adminStatsOverview(),
      adminListDoctors(),
      adminListDepartments(),
      adminMonitorQueues(),
    ])
      .then(([ov, doc, dep, q]) => {
        setOverview(ov.data);
        setDoctors(doc.data);
        setDepartments(dep.data);
        setQueues(q.data);
      })
      .catch((err) => setError(err.response?.data?.error || "Could not load dashboard data"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadAll();
    const interval = setInterval(loadAll, 15000);
    return () => clearInterval(interval);
  }, [loadAll]);

  const handleDoctorSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      if (editingId) {
        const { password, email, ...editable } = doctorForm; // eslint-disable-line no-unused-vars
        await adminEditDoctor(editingId, editable);
      } else {
        await adminAddDoctor(doctorForm);
      }
      setDoctorForm(emptyDoctorForm);
      setEditingId(null);
      loadAll();
    } catch (err) {
      setError(err.response?.data?.error || "Could not save doctor");
    }
  };

  const handleEditClick = (doc) => {
    setEditingId(doc.id);
    setDoctorForm({
      full_name: doc.full_name,
      email: doc.email,
      password: "",
      department_id: doc.department_id,
      specialization: doc.specialization || "",
      average_consultation_time: doc.average_consultation_time,
    });
  };

  const handleDeleteDoctor = async (id) => {
    if (!window.confirm("Delete this doctor? This cannot be undone.")) return;
    try {
      await adminDeleteDoctor(id);
      setError("");
      loadAll();
    } catch (err) {
      setError(err.response?.data?.error || "Could not delete doctor");
    }
  };

  const handleAddDepartment = async (e) => {
    e.preventDefault();
    if (!newDeptName.trim()) return;
    try {
      await adminCreateDepartment({ name: newDeptName.trim() });
      setNewDeptName("");
      setError("");
      loadAll();
    } catch (err) {
      setError(err.response?.data?.error || "Could not add department");
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container my-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h3>Admin Dashboard</h3>
        <Link to="/analytics" className="btn btn-primary-hospital">
          View Full Analytics
        </Link>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {overview && (
        <div className="row g-3 mb-4">
          <div className="col-6 col-md-4 col-lg-2"><StatCard label="Today's Patients" value={overview.todays_patients} icon="🧑‍⚕️" /></div>
          <div className="col-6 col-md-4 col-lg-2"><StatCard label="Waiting" value={overview.waiting_patients} icon="⏳" /></div>
          <div className="col-6 col-md-4 col-lg-2"><StatCard label="Doctors Available" value={overview.doctors_available} icon="🩺" /></div>
          <div className="col-6 col-md-4 col-lg-2"><StatCard label="Avg. Wait (min)" value={overview.current_average_waiting_time} icon="⏱️" /></div>
          <div className="col-6 col-md-4 col-lg-2"><StatCard label="Completed" value={overview.completed_consultations} icon="✅" /></div>
          <div className="col-6 col-md-4 col-lg-2"><StatCard label="Cancelled" value={overview.cancelled_appointments} icon="🚫" /></div>
        </div>
      )}

      <div className="row g-4 mb-4">
        <div className="col-lg-7">
          <div className="card-panel">
            <h5 className="mb-3">{editingId ? "Edit Doctor" : "Add Doctor"}</h5>
            <form onSubmit={handleDoctorSubmit}>
              <div className="row g-2">
                <div className="col-md-6">
                  <input
                    className="form-control mb-2"
                    placeholder="Full name"
                    value={doctorForm.full_name}
                    onChange={(e) => setDoctorForm({ ...doctorForm, full_name: e.target.value })}
                    required
                  />
                </div>
                <div className="col-md-6">
                  <input
                    type="email"
                    className="form-control mb-2"
                    placeholder="Email"
                    value={doctorForm.email}
                    onChange={(e) => setDoctorForm({ ...doctorForm, email: e.target.value })}
                    disabled={!!editingId}
                    required
                  />
                </div>
                {!editingId && (
                  <div className="col-md-6">
                    <input
                      type="password"
                      className="form-control mb-2"
                      placeholder="Password"
                      value={doctorForm.password}
                      onChange={(e) => setDoctorForm({ ...doctorForm, password: e.target.value })}
                      required
                      minLength={6}
                    />
                  </div>
                )}
                <div className="col-md-6">
                  <select
                    className="form-select mb-2"
                    value={doctorForm.department_id}
                    onChange={(e) => setDoctorForm({ ...doctorForm, department_id: e.target.value })}
                    required
                  >
                    <option value="">Select department</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
                <div className="col-md-6">
                  <input
                    className="form-control mb-2"
                    placeholder="Specialization"
                    value={doctorForm.specialization}
                    onChange={(e) => setDoctorForm({ ...doctorForm, specialization: e.target.value })}
                  />
                </div>
                <div className="col-md-6">
                  <input
                    type="number"
                    className="form-control mb-2"
                    placeholder="Avg. consultation time (min)"
                    value={doctorForm.average_consultation_time}
                    onChange={(e) => setDoctorForm({ ...doctorForm, average_consultation_time: e.target.value })}
                  />
                </div>
              </div>
              <div className="d-flex gap-2 mt-2">
                <button type="submit" className="btn btn-primary-hospital">
                  {editingId ? "Save Changes" : "Add Doctor"}
                </button>
                {editingId && (
                  <button
                    type="button"
                    className="btn btn-outline-secondary"
                    onClick={() => { setEditingId(null); setDoctorForm(emptyDoctorForm); }}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>

        <div className="col-lg-5">
          <div className="card-panel">
            <h5 className="mb-3">Departments</h5>
            <form className="d-flex gap-2 mb-3" onSubmit={handleAddDepartment}>
              <input
                className="form-control"
                placeholder="New department name"
                value={newDeptName}
                onChange={(e) => setNewDeptName(e.target.value)}
              />
              <button className="btn btn-primary-hospital" type="submit">Add</button>
            </form>
            <ul className="list-group">
              {departments.map((d) => (
                <li key={d.id} className="list-group-item d-flex justify-content-between">
                  <span>{d.name}</span>
                  <span className="text-muted small">{d.doctor_count} doctors</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <h5 className="mb-3">All Doctors</h5>
      {doctors.length === 0 ? (
        <EmptyState message="No doctors added yet." />
      ) : (
        <div className="card-panel p-0 mb-4">
          <table className="table mb-0 align-middle">
            <thead>
              <tr>
                <th>Name</th>
                <th>Department</th>
                <th>Specialization</th>
                <th>Load</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {doctors.map((d) => (
                <tr key={d.id}>
                  <td>{d.full_name}</td>
                  <td>{d.department_name}</td>
                  <td>{d.specialization}</td>
                  <td>{d.current_load}</td>
                  <td>{d.is_available ? <span className="badge bg-success">Available</span> : <span className="badge bg-danger">Unavailable</span>}</td>
                  <td>
                    <div className="d-flex gap-1">
                      <button className="btn btn-sm btn-outline-secondary" onClick={() => handleEditClick(d)}>Edit</button>
                      <button className="btn btn-sm btn-outline-danger" onClick={() => handleDeleteDoctor(d.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h5 className="mb-3">Live Queue Monitor ({queues.length})</h5>
      {queues.length === 0 ? (
        <EmptyState message="No active queues right now." />
      ) : (
        <div className="card-panel p-0">
          <table className="table mb-0">
            <thead>
              <tr>
                <th>Queue No.</th>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Department</th>
                <th>Status</th>
                <th>Est. Wait</th>
              </tr>
            </thead>
            <tbody>
              {queues.map((q) => (
                <tr key={q.id}>
                  <td>{q.queue_number}</td>
                  <td>{q.patient_name}</td>
                  <td>{q.doctor_name}</td>
                  <td>{q.department_name}</td>
                  <td><StatusBadge status={q.status} /></td>
                  <td>{q.predicted_waiting_time ? `${q.predicted_waiting_time} min` : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
