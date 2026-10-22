import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getErrorMessage } from "../api/api";

export default function Register() {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    password: "",
    gender: "",
    address: "",
    blood_group: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register(form);
      navigate("/patient");
    } catch (err) {
      setError(getErrorMessage(err, "Registration failed."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container my-5" style={{ maxWidth: 500 }}>
      <div className="card-panel">
        <h3 className="mb-4 text-center">Create Patient Account</h3>
        {error && <div className="alert alert-danger">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Full Name</label>
            <input name="full_name" className="form-control" value={form.full_name} onChange={handleChange} required />
          </div>
          <div className="mb-3">
            <label className="form-label">Email</label>
            <input type="email" name="email" className="form-control" value={form.email} onChange={handleChange} required />
          </div>
          <div className="mb-3">
            <label className="form-label">Phone</label>
            <input name="phone" className="form-control" value={form.phone} onChange={handleChange} />
          </div>
          <div className="row">
            <div className="col-md-6 mb-3">
              <label className="form-label">Gender</label>
              <select name="gender" className="form-select" value={form.gender} onChange={handleChange}>
                <option value="">Select</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="col-md-6 mb-3">
              <label className="form-label">Blood Group</label>
              <input name="blood_group" className="form-control" value={form.blood_group} onChange={handleChange} placeholder="e.g. O+" />
            </div>
          </div>
          <div className="mb-3">
            <label className="form-label">Address</label>
            <input name="address" className="form-control" value={form.address} onChange={handleChange} />
          </div>
          <div className="mb-3">
            <label className="form-label">Password</label>
            <input type="password" name="password" className="form-control" value={form.password} onChange={handleChange} required minLength={6} />
          </div>
          <button type="submit" className="btn btn-primary-hospital w-100" disabled={submitting}>
            {submitting ? "Creating account..." : "Register"}
          </button>
        </form>
        <p className="text-center mt-3 mb-0">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
}
