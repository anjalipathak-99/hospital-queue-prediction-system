import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:5000/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response && error.response.status;
    const hasToken = !!localStorage.getItem("token");
    if (hasToken && (status === 401 || status === 422)) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export const getErrorMessage = (err, fallback = "Something went wrong.") => {
  if (err?.response?.data?.error) return err.response.data.error;
  if (!err?.response) {
    return `Cannot reach the server at ${api.defaults.baseURL}. Make sure the Flask backend is running (python app.py) and CORS_ORIGINS includes this site.`;
  }
  return `${fallback} (server responded with HTTP ${err.response.status})`;
};

// ---------- Auth ----------
export const registerPatient = (data) => api.post("/auth/register", data);
export const login = (data) => api.post("/auth/login", data);
export const getMe = () => api.get("/auth/me");

// ---------- Patient ----------
export const getDepartments = () => api.get("/patient/departments");
export const getDoctors = (departmentId) =>
  api.get("/patient/doctors", { params: departmentId ? { department_id: departmentId } : {} });
export const getDoctor = (doctorId) => api.get(`/patient/doctors/${doctorId}`);
export const bookAppointment = (data) => api.post("/patient/appointments", data);
export const getMyAppointments = (status) =>
  api.get("/patient/appointments", { params: status ? { status } : {} });
export const getQueueStatus = (appointmentId) =>
  api.get(`/patient/appointments/${appointmentId}/queue-status`);
export const cancelAppointment = (appointmentId) =>
  api.post(`/patient/appointments/${appointmentId}/cancel`);
export const getPatientProfile = () => api.get("/patient/profile");
export const updatePatientProfile = (data) => api.put("/patient/profile", data);

// ---------- Doctor ----------
export const getDoctorQueue = () => api.get("/doctor/queue");
export const getDoctorTodaysAppointments = () => api.get("/doctor/appointments/today");
export const startConsultation = (appointmentId) =>
  api.post(`/doctor/appointments/${appointmentId}/start`);
export const completeConsultation = (appointmentId, notes) =>
  api.post(`/doctor/appointments/${appointmentId}/complete`, { notes });
export const skipPatient = (appointmentId) => api.post(`/doctor/appointments/${appointmentId}/skip`);
export const markAbsent = (appointmentId) => api.post(`/doctor/appointments/${appointmentId}/absent`);
export const getDoctorStats = () => api.get("/doctor/stats");
export const setDoctorAvailability = (isAvailable) =>
  api.put("/doctor/availability", { is_available: isAvailable });

// ---------- Admin ----------
export const adminListDepartments = () => api.get("/admin/departments");
export const adminCreateDepartment = (data) => api.post("/admin/departments", data);
export const adminUpdateDepartment = (id, data) => api.put(`/admin/departments/${id}`, data);
export const adminDeleteDepartment = (id) => api.delete(`/admin/departments/${id}`);

export const adminListDoctors = () => api.get("/admin/doctors");
export const adminAddDoctor = (data) => api.post("/admin/doctors", data);
export const adminEditDoctor = (id, data) => api.put(`/admin/doctors/${id}`, data);
export const adminDeleteDoctor = (id) => api.delete(`/admin/doctors/${id}`);

export const adminListPatients = () => api.get("/admin/patients");
export const adminListAppointments = (status) =>
  api.get("/admin/appointments", { params: status ? { status } : {} });
export const adminMonitorQueues = () => api.get("/admin/queues");

export const adminStatsOverview = () => api.get("/admin/stats/overview");
export const adminStatsPatientsPerDay = (days) =>
  api.get("/admin/stats/patients-per-day", { params: { days } });
export const adminStatsWaitByHour = () => api.get("/admin/stats/wait-by-hour");
export const adminStatsByDepartment = () => api.get("/admin/stats/by-department");
export const adminStatsDoctorWorkload = () => api.get("/admin/stats/doctor-workload");
export const adminStatsStatusBreakdown = () => api.get("/admin/stats/status-breakdown");
export const adminStatsPeakHours = () => api.get("/admin/stats/peak-hours");
export const adminStatsMonthly = (months) =>
  api.get("/admin/stats/monthly", { params: { months } });

// ---------- ML ----------
export const predictWaitingTime = (features) => api.post("/ml/predict", features);

export default api;
