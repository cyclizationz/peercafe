-- Migration: Create restaurants table
-- Description: Creates the restaurants table with all required fields including PostGIS geography support
-- Date: 2025-01-XX

-- Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create restaurants table
CREATE TABLE IF NOT EXISTS restaurants (
    restaurant_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    primary_admin_id TEXT,
    logo VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    description TEXT,
    address VARCHAR(500) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    cuisine_type VARCHAR(100) NOT NULL,
    rating DECIMAL(3,1) CHECK (rating >= 0 AND rating <= 5),
    delivery_fee DECIMAL(10,2) CHECK (delivery_fee >= 0),
    location GEOGRAPHY(POINT, 4326), -- PostGIS geography type for spatial queries
    latitude DOUBLE PRECISION CHECK (latitude >= -90 AND latitude <= 90),
    longitude DOUBLE PRECISION CHECK (longitude >= -180 AND longitude <= 180)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine_type ON restaurants(cuisine_type);
CREATE INDEX IF NOT EXISTS idx_restaurants_is_active ON restaurants(is_active);
CREATE INDEX IF NOT EXISTS idx_restaurants_rating ON restaurants(rating DESC);
CREATE INDEX IF NOT EXISTS idx_restaurants_address ON restaurants USING gin(to_tsvector('english', address));
CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants USING GIST(location); -- Spatial index for geography

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_restaurants_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_update_restaurants_updated_at
    BEFORE UPDATE ON restaurants
    FOR EACH ROW
    EXECUTE FUNCTION update_restaurants_updated_at();

-- Add comment to table
COMMENT ON TABLE restaurants IS 'Stores restaurant information including location data for delivery services';
COMMENT ON COLUMN restaurants.location IS 'PostGIS geography point for spatial queries (use latitude/longitude for text searches)';
COMMENT ON COLUMN restaurants.address IS 'Full address string for text-based location searches';

