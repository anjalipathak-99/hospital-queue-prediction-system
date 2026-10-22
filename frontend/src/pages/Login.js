import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getErrorMessage } from "../api/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const user = await login(email, password);
      if (user.role === "admin") navigate("/admin");
      else if (user.role === "doctor") navigate("/doctor");
      else navigate("/patient");
    } catch (err) {
      setError(getErrorMessage(err, "Login failed."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container my-5" style={{ maxWidth: 420 }}>
      <div className="card-panel">
        <h3 className="mb-4 text-center">Welcome Back</h3>
        {error && <div className="alert alert-danger">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Email</label>
            <input
              type="email"
              className="form-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="mb-3">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary-hospital w-100"
            disabled={submitting}
          >
            {submitting ? "Logging in..." : "Login"}
          </button>
        </form>
        <p className="text-center mt-3 mb-0">
          Don&apos;t have an account? <Link to="/register">Register</Link>
        </p>
        <hr />
        <p className="text-muted small mb-0">
          Demo accounts (after running <code>seed.py</code>): <br />
          Admin: admin@hospital.com / admin123 <br />
          Doctor: amit.sharma@hospital.com / doctor123 <br />
          Patient: rahul.sharma@example.com / patient123
        </p>
      </div>
    </div>
  );
}
