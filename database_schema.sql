-- Skema Database Sistem Pencatatan Penginapan Kos untuk MySQL

-- Tabel Users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel Properties
CREATE TABLE IF NOT EXISTS properties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200),
    total_rooms INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel Rooms
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    number VARCHAR(10) NOT NULL,
    property_id INT NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    monthly_rate INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id)
);

-- Tabel Occupancy Records
CREATE TABLE IF NOT EXISTS occupancy_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    month VARCHAR(7) NOT NULL,
    is_occupied BOOLEAN DEFAULT TRUE,
    tenant_name VARCHAR(100),
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_date DATE,
    payment_due_date DATE,
    payment_months INT DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (room_id) REFERENCES rooms(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Tabel Financial Records
CREATE TABLE IF NOT EXISTS financial_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    transaction_date DATE NOT NULL,
    amount INT NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,
    category VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (property_id) REFERENCES properties(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Tabel National Holidays
CREATE TABLE IF NOT EXISTS national_holidays (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indeks untuk Pencarian Cepat
CREATE INDEX idx_rooms_property_id ON rooms(property_id);
CREATE INDEX idx_occupancy_room_id ON occupancy_records(room_id);
CREATE INDEX idx_occupancy_month ON occupancy_records(month);
CREATE INDEX idx_financial_property_id ON financial_records(property_id);
CREATE INDEX idx_financial_transaction_date ON financial_records(transaction_date);

-- Data Awal (Opsional) - Admin User
INSERT IGNORE INTO users (username, password_hash, role)
VALUES ('admin', -- Ganti dengan hash password yang dihasilkan oleh aplikasi
        'pbkdf2:sha256:150000$abcdefgh$1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        'admin');

-- Data Properties Awal
INSERT IGNORE INTO properties (name, address, total_rooms)
VALUES 
    ('KOS ANTAPANI', 'Jl. Antapani No. 123, Bandung', 21),
    ('KOS GURO', 'Jl. Guro No. 456, Bandung', 32),
    ('KOS PESONA GRIYA', 'Jl. Pesona Griya No. 789, Bandung', 33);