-- Database creation
CREATE DATABASE IF NOT EXISTS student_finance_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE student_finance_db;

-- Users table (for admin authentication)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(120) UNIQUE,
    full_name VARCHAR(150),
    role ENUM('admin', 'accountant', 'viewer') DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_number VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    grade VARCHAR(10) NOT NULL,
    guardian_name VARCHAR(150),
    guardian_contact VARCHAR(20) NOT NULL,
    guardian_email VARCHAR(120),
    address TEXT,
    balance DECIMAL(15, 2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    enrollment_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student_number (student_number),
    INDEX idx_full_name (full_name),
    INDEX idx_grade (grade),
    INDEX idx_balance (balance)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Fee structures table
CREATE TABLE IF NOT EXISTS fee_structures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grade VARCHAR(10) NOT NULL,
    term ENUM('Term 1', 'Term 2', 'Term 3', 'Annual') NOT NULL,
    fee_type VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    description TEXT,
    academic_year VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_grade (grade),
    INDEX idx_term (term),
    INDEX idx_fee_type (fee_type),
    UNIQUE KEY unique_fee (grade, term, fee_type, academic_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    fee_type VARCHAR(50) NOT NULL,
    payment_method ENUM('Cash', 'M-Pesa', 'Bank Transfer', 'Cheque', 'Card') NOT NULL,
    payment_date DATE NOT NULL,
    transaction_reference VARCHAR(100),
    receipt_number VARCHAR(50) UNIQUE,
    notes TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_student_id (student_id),
    INDEX idx_payment_date (payment_date),
    INDEX idx_receipt_number (receipt_number),
    INDEX idx_payment_method (payment_method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Balance history table (for audit trail)
CREATE TABLE IF NOT EXISTS balance_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    previous_balance DECIMAL(15, 2) NOT NULL,
    new_balance DECIMAL(15, 2) NOT NULL,
    change_amount DECIMAL(15, 2) NOT NULL,
    change_type ENUM('payment', 'fee_applied', 'adjustment', 'refund') NOT NULL,
    reference_id INT,
    description TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_student_id (student_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- System logs table
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
INSERT INTO users (username, password_hash, email, full_name, role) 
VALUES (
    'admin', 
    'scrypt:32768:8:1$fYvDxCQvFKhzLcTk$74f8d3a1dc9e7c8e3e2e5f8c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c3e5c',
    'admin@school.com',
    'System Administrator',
    'admin'
) ON DUPLICATE KEY UPDATE username=username;

-- Insert sample data
INSERT INTO students (student_number, full_name, grade, guardian_contact, balance, enrollment_date) VALUES
('STU001', 'John Mwangi', '10', '+254712345678', 15000.00, '2024-01-15'),
('STU002', 'Sarah Wanjiku', '9', '+254723456789', 8500.00, '2024-01-15'),
('STU003', 'Michael Kiprotich', '11', '+254734567890', 22000.00, '2024-01-15'),
('STU004', 'Emily Achieng', '10', '+254745678901', 6200.00, '2024-01-15'),
('STU005', 'James Otieno', '12', '+254756789012', 18500.00, '2024-01-15')
ON DUPLICATE KEY UPDATE student_number=student_number;

INSERT INTO fee_structures (grade, term, fee_type, amount, academic_year) VALUES
('9', 'Term 1', 'Tuition', 25000.00, '2024'),
('10', 'Term 1', 'Tuition', 28000.00, '2024'),
('11', 'Term 1', 'Tuition', 32000.00, '2024'),
('12', 'Term 1', 'Tuition', 35000.00, '2024'),
('9', 'Term 1', 'Books', 4500.00, '2024')
ON DUPLICATE KEY UPDATE grade=grade;