"""
Generates a realistic synthetic dataset for hospital queue waiting-time prediction.

Run:
    python generate_dataset.py

Produces dataset.csv in the same folder (backend/ml/dataset.csv).

The data is not purely random - waiting_time_minutes is built from a plausible
formula involving the other features, plus noise, so a regressor can actually
learn meaningful relationships from it.
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

N_RECORDS = 4000

# appointment_type encoding: 0 = general, 1 = follow_up, 2 = emergency
# priority_level: 1 = normal, 2 = high, 3 = emergency
# day_of_week: 0 = Monday ... 6 = Sunday


def generate_dataset(n=N_RECORDS):
    day_of_week = RNG.integers(0, 7, size=n)

    # Hospitals are busiest 9am-1pm and 4pm-7pm; use a weighted distribution
    hour_choices = list(range(8, 20))
    hour_weights = np.array([
        1.0, 2.5, 3.0, 3.0, 2.5, 1.2, 1.0, 1.0, 1.5, 2.8, 3.2, 2.0
    ])
    hour_weights = hour_weights / hour_weights.sum()
    hour = RNG.choice(hour_choices, size=n, p=hour_weights)

    appointment_type = RNG.choice([0, 1, 2], size=n, p=[0.65, 0.25, 0.10])

    # priority mostly follows appointment type, with some independent variance
    priority_level = np.where(
        appointment_type == 2,
        3,
        RNG.choice([1, 2], size=n, p=[0.8, 0.2]),
    )

    average_consultation_time = np.clip(
        RNG.normal(loc=15, scale=4, size=n), 5, 40
    ).round(1)

    doctor_current_load = RNG.integers(0, 25, size=n)

    # patients_ahead correlates with doctor_current_load but has its own noise
    patients_ahead = np.clip(
        (doctor_current_load * RNG.uniform(0.6, 1.1, size=n)) + RNG.integers(-3, 6, size=n),
        0,
        None,
    ).round().astype(int)

    doctor_available = RNG.choice([0, 1], size=n, p=[0.08, 0.92])

    # historical_average_wait: baseline for this doctor/department/time-slot
    historical_average_wait = np.clip(
        RNG.normal(loc=25, scale=8, size=n), 5, 90
    ).round(1)

    # --- Core formula for waiting_time_minutes ---
    base = patients_ahead * average_consultation_time * 0.9
    load_penalty = doctor_current_load * 1.3
    unavailable_penalty = np.where(doctor_available == 0, 45, 0)
    priority_discount = np.select(
        [priority_level == 3, priority_level == 2, priority_level == 1],
        [-0.85, -0.35, 0.0],
    )
    history_blend = historical_average_wait * 0.35

    # weekends / evenings run slightly faster (fewer walk-ins after peak)
    weekend_effect = np.where(day_of_week >= 5, -4, 0)
    evening_effect = np.where(hour >= 17, -3, 0)

    noise = RNG.normal(loc=0, scale=6, size=n)

    waiting_time_minutes = (
        base
        + load_penalty
        + unavailable_penalty
        + history_blend
        + weekend_effect
        + evening_effect
        + noise
    )
    # apply priority discount as a percentage reduction (emergencies jump the queue)
    waiting_time_minutes = waiting_time_minutes * (1 + priority_discount)
    waiting_time_minutes = np.clip(waiting_time_minutes, 2, 240).round(1)

    df = pd.DataFrame(
        {
            "patients_ahead": patients_ahead,
            "average_consultation_time": average_consultation_time,
            "doctor_available": doctor_available,
            "appointment_type": appointment_type,
            "priority_level": priority_level,
            "day_of_week": day_of_week,
            "hour": hour,
            "doctor_current_load": doctor_current_load,
            "historical_average_wait": historical_average_wait,
            "waiting_time_minutes": waiting_time_minutes,
        }
    )
    return df


if __name__ == "__main__":
    df = generate_dataset()
    df.to_csv("dataset.csv", index=False)
    print(f"Generated {len(df)} records -> dataset.csv")
    print(df.describe())
