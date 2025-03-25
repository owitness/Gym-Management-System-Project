-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role ENUM('admin', 'trainer', 'member', 'non_member'),
    name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    zipcode VARCHAR(10) NOT NULL,
    membership_expiry DATE,
    auto_payment TINYINT(1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create classes table
CREATE TABLE IF NOT EXISTS classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(100) NOT NULL,
    trainer_id INT,
    schedule_time DATETIME NOT NULL,
    capacity INT NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES users(id)
);

-- Create memberships table
CREATE TABLE IF NOT EXISTS memberships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    start_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    status ENUM('active', 'expired', 'pending'),
    FOREIGN KEY (member_id) REFERENCES users(id)
);

-- Create payment_methods table
CREATE TABLE IF NOT EXISTS payment_methods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    card_number VARCHAR(16) NOT NULL,
    exp DATE NOT NULL,
    cvv VARCHAR(3) NOT NULL,
    card_holder_name VARCHAR(100) NOT NULL,
    saved TINYINT(1),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status ENUM('Completed', 'Pending', 'Failed'),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method_id INT,
    membership_duration INT NOT NULL,
    membership_expiry DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id)
);

-- Create attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_out_time TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES users(id)
);

-- Create class_bookings table
CREATE TABLE IF NOT EXISTS class_bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    class_id INT NOT NULL,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES users(id),
    FOREIGN KEY (class_id) REFERENCES classes(id)
);

-- Create indexes
ALTER TABLE users ADD INDEX idx_users_email (email);
ALTER TABLE memberships ADD INDEX idx_memberships_user_id (member_id);
ALTER TABLE payments ADD INDEX idx_payments_user_id (user_id);
ALTER TABLE payments ADD INDEX idx_payments_payment_method_id (payment_method_id);
ALTER TABLE attendance ADD INDEX idx_attendance_member_id (member_id);
ALTER TABLE class_bookings ADD INDEX idx_class_bookings_member_id (member_id);
ALTER TABLE class_bookings ADD INDEX idx_class_bookings_class_id (class_id); 