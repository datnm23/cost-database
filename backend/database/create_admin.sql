-- Create admin user for BOQ System
-- Password: admin123

-- Delete existing admin if exists
DELETE FROM users WHERE username = 'admin';

-- Insert admin user with hashed password
INSERT INTO users (username, email, full_name, hashed_password, role, is_active) 
VALUES (
    'admin', 
    'admin@boqsystem.com', 
    'System Administrator', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJhiPm.4VW6',
    'super_admin',
    1
);

-- Show result
SELECT 'Admin user created successfully!' as status;
SELECT user_id, username, email, full_name, role, is_active, created_at 
FROM users 
WHERE username = 'admin';
