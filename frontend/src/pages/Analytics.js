import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart, Line,
  BarChart, Bar,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import {
  adminStatsPatientsPerDay,
  adminStatsWaitByHour,
  adminStatsByDepartment,
  adminStatsDoctorWorkload,
  adminStatsStatusBreakdown,
} from "../api/api";
import { LoadingSpinner } from "../components/Widgets";

const COLORS = ["#0f7a6e", "#2f8fd6", "#e0a734", "#e0554f", "#8e6fd6", "#4fae7c"];

export default function Analytics() {
  const [patientsPerDay, setPatientsPerDay] = useState([]);
  const [waitByHour, setWaitByHour] = useState([]);
  const [byDepartment, setByDepartment] = useState([]);
  const [workload, setWorkload] = useState([]);
  const [statusBreakdown, setStatusBreakdown] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      adminStatsPatientsPerDay(14),
      adminStatsWaitByHour(),
      adminStatsByDepartment(),
      adminStatsDoctorWorkload(),
      adminStatsStatusBreakdown(),
    ])
      .then(([ppd, wbh, dept, load, status]) => {
        setPatientsPerDay(ppd.data);
        setWaitByHour(wbh.data);
        setByDepartment(dept.data);
        setWorkload(load.data);
        setStatusBreakdown(status.data);
      })
      .catch((err) => setError(err.response?.data?.error || "Could not load analytics data"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="container my-4">
      <h3 className="mb-4">Hospital Analytics</h3>
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="row g-4">
        <div className="col-lg-6">
          <div className="card-panel">
            <h6>Patients Per Day (last 14 days)</h6>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={patientsPerDay}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#0f7a6e" strokeWidth={2} name="Patients" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="card-panel">
            <h6>Average Waiting Time by Hour</h6>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={waitByHour}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" tick={{ fontSize: 11 }} label={{ value: "Hour", position: "insideBottom", offset: -2 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="avg_wait" fill="#2f8fd6" name="Avg Wait (min)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="card-panel">
            <h6>Patients by Department</h6>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={byDepartment}
                  dataKey="count"
                  nameKey="department"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={(entry) => entry.department}
                >
                  {byDepartment.map((entry, index) => (
                    <Cell key={entry.department} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="card-panel">
            <h6>Doctor Workload (Today)</h6>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={workload} layout="vertical" margin={{ left: 40 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="doctor_name" tick={{ fontSize: 11 }} width={120} />
                <Tooltip />
                <Bar dataKey="patients_today" fill="#e0a734" name="Patients" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-12">
          <div className="card-panel">
            <h6>Appointment Status Breakdown (Today)</h6>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={statusBreakdown}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={(entry) => entry.status}
                >
                  {statusBreakdown.map((entry, index) => (
                    <Cell key={entry.status} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
