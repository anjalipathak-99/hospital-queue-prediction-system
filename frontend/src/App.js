import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import PatientDashboard from "./pages/PatientDashboard";
import DoctorList from "./pages/DoctorList";
import BookAppointment from "./pages/BookAppointment";
import QueueStatus from "./pages/QueueStatus";
import AppointmentHistory from "./pages/AppointmentHistory";
import DoctorDashboard from "./pages/DoctorDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import Analytics from "./pages/Analytics";
import Profile from "./pages/Profile";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Navbar />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Patient routes */}
          <Route
            path="/patient"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <PatientDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/doctors"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <DoctorList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/book/:doctorId"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <BookAppointment />
              </ProtectedRoute>
            }
          />
          <Route
            path="/queue/:appointmentId"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <QueueStatus />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <AppointmentHistory />
              </ProtectedRoute>
            }
          />

          {/* Doctor routes */}
          <Route
            path="/doctor"
            element={
              <ProtectedRoute allowedRoles={["doctor"]}>
                <DoctorDashboard />
              </ProtectedRoute>
            }
          />

          {/* Admin routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <Analytics />
              </ProtectedRoute>
            }
          />

          {/* Shared */}
          <Route
            path="/profile"
            element={
              <ProtectedRoute allowedRoles={["patient", "doctor", "admin"]}>
                <Profile />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
