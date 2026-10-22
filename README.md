# MediQueue — Hospital Queue Prediction System

A full-stack hospital queue management system where the **central feature is a
Machine Learning model (Random Forest Regressor)** that predicts each
patient's waiting time in real time, based on live queue state, doctor load,
priority, and historical patterns.

- **Frontend:** React, React Router, Axios, Recharts, Bootstrap
- **Backend:** Python, Flask, REST APIs, JWT authentication
- **Database:** MySQL (via SQLAlchemy + PyMySQL)
- **ML:** Pandas, NumPy, Scikit-learn (Random Forest Regressor), Joblib

---

## 1. Project Structure

```
hospital-queue-system/
├── backend/
│   ├── app.py                 # Flask app factory + entrypoint
│   ├── config.py              # Config (DB, JWT, CORS, ML paths)
│   ├── extensions.py          # SQLAlchemy / JWT / CORS / Bcrypt singletons
│   ├── seed.py                # Creates tables + seeds admin/doctors/patient
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/                # SQLAlchemy models
│   ├── routes/                # auth, patient, doctor, admin, appointments, queues, ml
│   ├── services/               # queue_service.py, stats_service.py (business logic)
│   ├── ml/
│   │   ├── generate_dataset.py  # synthetic dataset generator
│   │   ├── dataset.csv          # generated training data (4,000 rows)
│   │   ├── train.py             # trains + evaluates the Random Forest model
│   │   ├── predict.py           # loads model.pkl, exposes predict_waiting_time()
│   │   ├── model.pkl            # trained model (pre-built, included)
│   │   └── metrics.json         # MAE / RMSE / R² from the last training run
│   ├── utils/                  # decorators (role auth), validators
│   └── sql/schema.sql          # MySQL DDL (reference / manual setup)
└── frontend/
    ├── package.json
    ├── public/index.html
    ├── .env.example
    └── src/
        ├── api/api.js           # Axios client, one function per endpoint
        ├── context/AuthContext.js
        ├── components/          # Navbar, ProtectedRoute, StatCard, StatusBadge...
        ├── pages/                # Landing, Login, Register, dashboards, etc.
        └── styles/app.css
```

---

## 2. Prerequisites

- Python 3.10 – 3.12 (the pinned numpy/scikit-learn versions have no wheels for 3.13+)
- Node.js 18+ and npm
- MySQL 8.x running locally (or a reachable MySQL instance)

---

## 3. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create the database:

```sql
CREATE DATABASE hospital_queue_db CHARACTER SET utf8mb4;
```

Configure your connection — copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
# then edit DB_USER / DB_PASSWORD / DB_HOST / DB_NAME to match your MySQL setup
```

`config.py` loads `backend/.env` automatically (via `python-dotenv`) and falls back to
local defaults, so `python app.py`, `python seed.py` and `gunicorn app:app` all pick up your
settings. Real environment variables take precedence over the file. Set `APP_TIMEZONE`
(default `Asia/Kolkata`) to your hospital's IANA timezone - "today", queue hours and the
analytics all use it.

> **Upgrading from the earlier version?** Timestamps are now stored in `APP_TIMEZONE` instead of
> UTC and one foreign key changed, so drop and recreate the database
> (`DROP DATABASE hospital_queue_db; CREATE DATABASE hospital_queue_db CHARACTER SET utf8mb4;`)
> and run `python seed.py` again.

Create the tables and seed demo data (admin, 5 departments, 5 doctors, 1 patient):

```bash
python seed.py
```

This prints the demo credentials it creates:

```
Admin:    admin@hospital.com   / admin123
Doctor:   amit.sharma@hospital.com / doctor123 (+ 4 more doctors)
Patient:  rahul.sharma@example.com / patient123
```

**ML model** — a trained `model.pkl` is already included in `backend/ml/`.
To regenerate the dataset and retrain from scratch:

```bash
cd ml
python generate_dataset.py   # writes dataset.csv (4,000 synthetic records)
python train.py              # trains RandomForestRegressor, evaluates, saves model.pkl
```

Last training run achieved: **MAE ≈ 4.9 min, RMSE ≈ 7.4 min, R² ≈ 0.99**
(see `backend/ml/metrics.json`).

Run the backend:

```bash
cd backend        # if you're inside ml/, cd ..
python app.py
```

The API is now live at `http://localhost:5000`. Health check:
`GET http://localhost:5000/api/health`

---

## 4. Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env   # REACT_APP_API_URL=http://localhost:5000/api
npm start
```

The app runs at `http://localhost:3000` and proxies API calls to the Flask
backend.

---

## 5. Using the App

1. Go to `http://localhost:3000`.
2. Register a new patient account, or log in with the seeded demo accounts
   listed above.
3. **As a patient:** browse doctors → book an appointment → see your live
   queue number, patients ahead, and ML-predicted waiting time → track it on
   the live-updating queue status page.
4. **As a doctor:** log in and view your live waiting queue → Start /
   Complete / Skip / Mark Absent on each patient → the queue automatically
   re-predicts waiting times for everyone behind them.
5. **As an admin:** manage departments and doctors, monitor all active
   queues hospital-wide, and view analytics (patients/day, wait time by
   hour, department load, doctor workload, status breakdown).

---

## 6. Key API Endpoints

| Area | Method & Path | Description |
|---|---|---|
| Auth | `POST /api/auth/register` | Register a patient |
| Auth | `POST /api/auth/login` | Login, returns JWT |
| Auth | `GET /api/auth/me` | Current user info |
| Patient | `GET /api/patient/doctors` | List doctors (optional `?department_id=`) |
| Patient | `POST /api/patient/appointments` | Book appointment → returns queue number + ML prediction |
| Patient | `GET /api/patient/appointments/:id/queue-status` | Live position, patients ahead, predicted wait |
| Patient | `POST /api/patient/appointments/:id/cancel` | Cancel a waiting appointment |
| Doctor | `GET /api/doctor/queue` | Today's live queue |
| Doctor | `POST /api/doctor/appointments/:id/start` | Start consultation |
| Doctor | `POST /api/doctor/appointments/:id/complete` | Complete consultation (recalculates queue) |
| Doctor | `POST /api/doctor/appointments/:id/skip` | Skip patient |
| Doctor | `POST /api/doctor/appointments/:id/absent` | Mark absent |
| Admin | `POST /api/admin/doctors` | Add doctor |
| Admin | `GET /api/admin/stats/overview` | Dashboard summary cards |
| Admin | `GET /api/admin/stats/*` | Charts data (patients/day, wait/hour, by department, workload, status, peak hours) |
| ML | `POST /api/ml/predict` | Raw feature vector → predicted waiting time |

Example `POST /api/ml/predict` body/response:

```json
// Request
{
  "patients_ahead": 17,
  "average_consultation_time": 15,
  "doctor_available": 1,
  "appointment_type": 0,
  "priority_level": 1,
  "day_of_week": 2,
  "hour": 11,
  "doctor_current_load": 12,
  "historical_average_wait": 28
}

// Response
{
  "patients_ahead": 17,
  "predicted_waiting_time": 52.3,
  "unit": "minutes",
  "model_trained": true
}
```

All non-auth endpoints require `Authorization: Bearer <token>`.

---

## 7. How the ML Prediction Works

1. `backend/ml/generate_dataset.py` builds a realistic synthetic dataset
   (patients ahead, doctor load, consultation time, priority, time of day,
   etc. → waiting_time_minutes), since no real hospital dataset was supplied.
2. `backend/ml/train.py` splits the data 80/20, grid-searches a
   `RandomForestRegressor` over `n_estimators`, `max_depth`, and
   `min_samples_leaf`, and evaluates with **MAE**, **RMSE**, and **R²**.
   The trained model + feature list are saved together to `model.pkl`.
3. `backend/ml/predict.py` loads `model.pkl` once and exposes
   `predict_waiting_time(features)`, with a heuristic fallback if the model
   hasn't been trained yet so the API never crashes.
4. `backend/services/queue_service.py` builds the live feature vector
   (patients ahead, doctor's current load, availability, historical average
   wait for that doctor, day/hour, etc.) every time a patient books an
   appointment, or whenever the queue changes (a consultation completes,
   someone is skipped/absent/cancelled) — so **every waiting patient's ETA
   updates automatically as the queue moves**.
5. Each prediction (and, later, the real observed wait) is logged to the
   `waiting_time_history` table, so the dataset can be extended with real
   data over time and the model periodically retrained.

---

## 8. Security Notes

- Passwords are hashed with bcrypt (`Flask-Bcrypt`) — never stored in plain text.
- JWT access tokens (8h expiry) carry the user's `role` claim; `role_required()`
  decorators enforce role-based authorization on every protected route.
- All input is validated (`utils/validators.py`) before hitting the database.
- CORS is restricted to the configured frontend origin.

---

## 9. Running Everything Together (quick reference)

```bash
# Terminal 1 - backend
cd backend
source venv/bin/activate
python seed.py          # first time only
python app.py

# Terminal 2 - frontend
cd frontend
npm start
```

Then open `http://localhost:3000`.
