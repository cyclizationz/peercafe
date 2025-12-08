-- Migration: Create users table
-- Description: Creates the users table for customer and delivery user accounts
-- Date: 2025-01-XX

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(50),
    is_admin BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    password TEXT NOT NULL, -- Hashed password (bcrypt)
    -- Address fields for delivery
    street VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    -- Location coordinates
    latitude DOUBLE PRECISION CHECK (latitude >= -90 AND latitude <= 90),
    longitude DOUBLE PRECISION CHECK (longitude >= -180 AND longitude <= 180),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_users_updated_at();

-- Add comment to table
COMMENT ON TABLE users IS 'Stores user accounts for customers and delivery personnel';
COMMENT ON COLUMN users.password IS 'Bcrypt hashed password - never store plain text';

