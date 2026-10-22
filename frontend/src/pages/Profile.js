import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getPatientProfile, updatePatientProfile } from "../api/api";
import { LoadingSpinner } from "../components/Widgets";

export default function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (user?.role === "patient") {
      getPatientProfile()
        .then((res) => setProfile(res.data))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [user]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const res = await updatePatientProfile({
        full_name: profile.full_name,
        phone: profile.phone,
        address: profile.address,
        blood_group: profile.blood_group,
        gender: profile.gender,
      });
      setProfile(res.data);
      setMessage("Profile updated successfully.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  if (user?.role !== "patient") {
    return (
      <div className="container my-4" style={{ maxWidth: 480 }}>
        <div className="card-panel">
          <h4>My Profile</h4>
          <hr />
          <p><strong>Name:</strong> {user.full_name}</p>
          <p><strong>Email:</strong> {user.email}</p>
          <p className="text-capitalize"><strong>Role:</strong> {user.role}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container my-4" style={{ maxWidth: 480 }}>
      <div className="card-panel">
        <h4>My Profile</h4>
        <hr />
        {message && <div className="alert alert-success">{message}</div>}
        <form onSubmit={handleSave}>
          <div className="mb-3">
            <label className="form-label">Full Name</label>
            <input
              className="form-control"
              value={profile.full_name || ""}
              onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
            />
          </div>
          <div className="mb-3">
            <label className="form-label">Email</label>
            <input className="form-control" value={profile.email || ""} disabled />
          </div>
          <div className="mb-3">
            <label className="form-label">Phone</label>
            <input
              className="form-control"
              value={profile.phone || ""}
              onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
            />
          </div>
          <div className="mb-3">
            <label className="form-label">Address</label>
            <input
              className="form-control"
              value={profile.address || ""}
              onChange={(e) => setProfile({ ...profile, address: e.target.value })}
            />
          </div>
          <div className="row">
            <div className="col-6 mb-3">
              <label className="form-label">Gender</label>
              <select
                className="form-select"
                value={profile.gender || ""}
                onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
              >
                <option value="">Select</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="col-6 mb-3">
              <label className="form-label">Blood Group</label>
              <input
                className="form-control"
                value={profile.blood_group || ""}
                onChange={(e) => setProfile({ ...profile, blood_group: e.target.value })}
              />
            </div>
          </div>
          <button className="btn btn-primary-hospital w-100" disabled={saving}>
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );
}
