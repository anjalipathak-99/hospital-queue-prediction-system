-- Hospital Queue Prediction System - MySQL schema
-- Note: running `python seed.py` will auto-create these tables via SQLAlchemy.
-- This file is provided for manual setup / reference / documentation.

CREATE DATABASE IF NOT EXISTS hospital_queue_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE hospital_queue_db;

-- ---------------------------------------------------------------
-- users
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('patient', 'doctor', 'admin') NOT NULL DEFAULT 'patient',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- departments
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- patients
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    date_of_birth DATE,
    gender ENUM('male', 'female', 'other'),
    address VARCHAR(255),
    blood_group VARCHAR(5),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- doctors
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    department_id INT NOT NULL,
    specialization VARCHAR(150),
    average_consultation_time INT DEFAULT 15,
    is_available BOOLEAN DEFAULT TRUE,
    max_daily_patients INT DEFAULT 40,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- appointments
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    queue_number INT NOT NULL,
    appointment_type ENUM('general', 'follow_up', 'emergency') DEFAULT 'general',
    priority_level INT DEFAULT 1,
    status ENUM('waiting', 'consulting', 'completed', 'cancelled', 'skipped', 'absent') DEFAULT 'waiting',
    predicted_waiting_time FLOAT,
    actual_waiting_time FLOAT,
    consultation_started_at DATETIME,
    consultation_ended_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    INDEX idx_appt_status (status),
    INDEX idx_appt_created (created_at),
    INDEX idx_appt_doctor_date (doctor_id, created_at)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- consultations
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS consultations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL UNIQUE,
    notes TEXT,
    duration_minutes FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- waiting_time_history  (ML training / retraining data)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS waiting_time_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT,
    patients_ahead INT NOT NULL,
    average_consultation_time FLOAT NOT NULL,
    doctor_available TINYINT NOT NULL,
    appointment_type TINYINT NOT NULL,
    priority_level INT NOT NULL,
    day_of_week INT NOT NULL,
    hour INT NOT NULL,
    doctor_current_load INT NOT NULL,
    historical_average_wait FLOAT NOT NULL,
    predicted_waiting_time FLOAT,
    actual_waiting_time_minutes FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE SET NULL
) ENGINE=InnoDB;
