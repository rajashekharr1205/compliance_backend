CREATE DATABASE IF NOT EXISTS compliance_db;
USE compliance_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    designation VARCHAR(100),
    email VARCHAR(100) UNIQUE NOT NULL,
    registration_id VARCHAR(50),
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    report_name VARCHAR(255) NOT NULL,
    transcript TEXT,
    score INT,
    verdict VARCHAR(50),
    duration VARCHAR(20),
    recording_url VARCHAR(255),
    patient_info TEXT,
    folder_name VARCHAR(100) DEFAULT 'Audits',
    timestamp BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
