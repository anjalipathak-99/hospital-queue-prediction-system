import React from "react";
import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div>
      <div className="landing-hero text-center">
        <div className="container">
          <h1 className="display-5 fw-bold">Smarter Hospital Queues, Powered by ML</h1>
          <p className="lead mt-3">
            MediQueue predicts your waiting time in real time, so you know exactly when to expect
            to be seen &mdash; no more guessing in the waiting room.
          </p>
          <div className="mt-4">
            <Link to="/register" className="btn btn-light btn-lg me-3">
              Book an Appointment
            </Link>
            <Link to="/login" className="btn btn-outline-light btn-lg">
              Login
            </Link>
          </div>
        </div>
      </div>

      <div className="container my-5">
        <div className="row g-4">
          <div className="col-md-4">
            <div className="card-panel h-100">
              <h5>🎯 ML-Powered Predictions</h5>
              <p className="text-muted mb-0">
                A Random Forest model trained on historical queue data estimates your waiting
                time using live doctor load, priority, and time-of-day patterns.
              </p>
            </div>
          </div>
          <div className="col-md-4">
            <div className="card-panel h-100">
              <h5>⏱️ Real-Time Queue Tracking</h5>
              <p className="text-muted mb-0">
                See your live queue number, patients ahead of you, and status updates the moment
                your doctor starts or completes a consultation.
              </p>
            </div>
          </div>
          <div className="col-md-4">
            <div className="card-panel h-100">
              <h5>📊 Hospital-Wide Analytics</h5>
              <p className="text-muted mb-0">
                Admins get full visibility into department load, doctor workload, peak hours, and
                daily/monthly statistics.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
