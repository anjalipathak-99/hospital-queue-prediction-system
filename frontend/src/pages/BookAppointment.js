import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getDoctor, bookAppointment } from "../api/api";
import { LoadingSpinner } from "../components/Widgets";

export default function BookAppointment() {
  const { doctorId } = useParams();
  const navigate = useNavigate();
  const [doctor, setDoctor] = useState(null);
  const [appointmentType, setAppointmentType] = useState("general");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getDoctor(doctorId)
      .then((res) => setDoctor(res.data))
      .catch((err) => setError(err.response?.data?.error || "Could not load doctor details."));
  }, [doctorId]);

  const handleBook = async () => {
    setError("");
    setSubmitting(true);
    try {
      const res = await bookAppointment({ doctor_id: doctorId, appointment_type: appointmentType });
      navigate(`/queue/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.error || "Booking failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!doctor && error) {
    return (
      <div className="container my-4" style={{ maxWidth: 500 }}>
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  }
  if (!doctor) return <LoadingSpinner />;

  return (
    <div className="container my-4" style={{ maxWidth: 500 }}>
      <div className="card-panel">
        <h4>Book Appointment</h4>
        <hr />
        <p>
          <strong>{doctor.full_name}</strong> &mdash; {doctor.specialization}
          <br />
          <span className="text-muted">{doctor.department_name}</span>
        </p>
        <p className="small text-muted">
          Current queue load: {doctor.current_load} patients &middot; Avg. consultation time:{" "}
          {doctor.average_consultation_time} min
        </p>

        {error && <div className="alert alert-danger">{error}</div>}

        <label className="form-label mt-2">Appointment Type</label>
        <select
          className="form-select mb-3"
          value={appointmentType}
          onChange={(e) => setAppointmentType(e.target.value)}
        >
          <option value="general">General Consultation</option>
          <option value="follow_up">Follow-up Visit</option>
          <option value="emergency">Emergency</option>
        </select>

        <button className="btn btn-primary-hospital w-100" onClick={handleBook} disabled={submitting}>
          {submitting ? "Booking..." : "Confirm Booking"}
        </button>
      </div>
    </div>
  );
}
