import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDepartments, getDoctors } from "../api/api";
import { LoadingSpinner, EmptyState } from "../components/Widgets";

export default function DoctorList() {
  const [departments, setDepartments] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [selectedDept, setSelectedDept] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDepartments().then((res) => setDepartments(res.data));
  }, []);

  useEffect(() => {
    setLoading(true);
    getDoctors(selectedDept || undefined)
      .then((res) => setDoctors(res.data))
      .finally(() => setLoading(false));
  }, [selectedDept]);

  return (
    <div className="container my-4">
      <h3 className="mb-4">Find a Doctor</h3>

      <div className="mb-4" style={{ maxWidth: 320 }}>
        <label className="form-label">Filter by Department</label>
        <select
          className="form-select"
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
        >
          <option value="">All Departments</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : doctors.length === 0 ? (
        <EmptyState message="No doctors found for this department." />
      ) : (
        <div className="row g-3">
          {doctors.map((doc) => (
            <div className="col-md-4" key={doc.id}>
              <div className="doctor-card">
                <h5>{doc.full_name}</h5>
                <div className="text-muted small mb-2">{doc.specialization}</div>
                <div className="mb-2">
                  <span className="badge bg-secondary">{doc.department_name}</span>{" "}
                  {doc.is_available ? (
                    <span className="badge bg-success">Available</span>
                  ) : (
                    <span className="badge bg-danger">Unavailable</span>
                  )}
                </div>
                <div className="small text-muted mb-3">
                  Current queue load: <strong>{doc.current_load}</strong> patients
                </div>
                <Link to={`/book/${doc.id}`} className="btn btn-primary-hospital w-100">
                  Book Appointment
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
