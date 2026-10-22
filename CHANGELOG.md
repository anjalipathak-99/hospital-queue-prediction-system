# Fixes in this version

## Backend
- **`.env` was never loaded** with `python app.py` / `python seed.py` / gunicorn, so the app always tried
  `root:password@localhost` -> "Access denied". `config.py` now calls `load_dotenv()`.
- **`cryptography` was missing** from requirements. PyMySQL needs it for MySQL 8's default
  `caching_sha2_password` login (error: *'cryptography' package is required ...*).
- DB passwords containing `@ : / #` broke the connection URL -> now URL-encoded; `mysql://` URLs from hosts are accepted.
- **Wrong "patients ahead" / queue position**: later arrivals of the same priority were counted as ahead of you,
  and every waiting patient got the *same* ML prediction. Position now matches the doctor's queue order
  (consulting first, then priority DESC, queue number ASC) and each patient is predicted for their own position.
- **Timezone mismatch**: rows were stamped in UTC but filtered by the server's local date, so appointments made
  between local midnight and the UTC offset (00:00-05:30 in India) vanished from "today's" queue, and the ML model
  received the UTC hour. Everything now uses one clock (`utils/timeutils.py`, `APP_TIMEZONE`).
- Deleting a doctor/patient with appointments crashed (FK from `waiting_time_history`) -> `ON DELETE SET NULL`.
- Deleting a department that still has doctors crashed -> clear 409 error. Duplicate department rename -> 409.
- Doctor/patient endpoints crashed (500) when the profile row was missing; patient `priority_level` garbage -> 400.
- Admin doctor form: numeric fields are validated; department checked on edit.
- A doctor could start several consultations at once (the UI assumed one) -> 409.
- Monthly stats returned the *oldest* N months instead of the latest N.
- `ml/predict.py`: uses a DataFrame (no feature-name warnings), and falls back to the heuristic instead of crashing
  if `model.pkl` can't be loaded (e.g. scikit-learn version mismatch). Added `ml/__init__.py`.
- Admin "Live Queue Monitor" shows today's active queues only.

- **"Registration failed. Please try again." with no reason**: unexpected errors (most often MySQL not running,
  wrong credentials, or tables not created) returned an HTML debug page, so the UI had nothing to show.
  The API now always answers with JSON and a clear message (e.g. "Database error: check that MySQL is running...").
- Register: blank gender/phone/address/blood group are stored as NULL (an empty gender string is rejected by the
  MySQL enum); e-mail is trimmed and compared case-insensitively; duplicate sign-ups return 409.
- Profile update with an empty gender no longer crashes.

## Frontend
- Login/Register now say *why* a request failed (e.g. "Cannot reach the server at http://localhost:5000/api...").
- Bootstrap JS was never imported, so the mobile navbar menu button did nothing.
- Doctor dashboard availability switch always started as "Available" regardless of the database.
- Queue status / booking / analytics / admin pages no longer hang on a spinner or swallow errors when a request fails.
- Expired/invalid tokens (HTTP 422) now log the user out cleanly.
