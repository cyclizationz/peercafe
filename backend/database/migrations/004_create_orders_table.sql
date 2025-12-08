-- Migration: Create orders table
-- Description: Creates the orders table for delivery-only orders with comprehensive tracking
-- Date: 2025-01-XX

CREATE TABLE IF NOT EXISTS orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    delivery_user_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(restaurant_id) ON DELETE RESTRICT,
    
    -- Order Items as JSONB (efficient for queries and storage)
    -- Structure: [{"item_id": int, "item_name": str, "price": decimal, "quantity": int, "subtotal": decimal, "special_instructions": str}]
    order_items JSONB NOT NULL,
    
    -- Pricing breakdown
    subtotal DECIMAL(10,2) NOT NULL CHECK (subtotal >= 0),
    tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    delivery_fee DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (delivery_fee >= 0),
    tip_amount DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (tip_amount >= 0),
    discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
    
    -- Order details (delivery-only, address always required)
    -- Structure: {"street": str, "city": str, "state": str, "zip_code": str, "instructions": str}
    delivery_address JSONB NOT NULL,
    payment_method TEXT NOT NULL DEFAULT 'cash_on_delivery',
    
    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'confirmed', 'preparing', 'ready', 
        'assigned', 'picked_up', 'en_route', 'delivered', 'cancelled'
    )),
    
    -- Timing
    estimated_pickup_time TIMESTAMPTZ,
    estimated_delivery_time TIMESTAMPTZ,
    actual_pickup_time TIMESTAMPTZ,
    actual_delivery_time TIMESTAMPTZ,
    
    -- Location tracking
    latitude DOUBLE PRECISION CHECK (latitude >= -90 AND latitude <= 90),
    longitude DOUBLE PRECISION CHECK (longitude >= -180 AND longitude <= 180),
    
    -- Distance and duration (from restaurant to delivery address)
    distance_restaurant_delivery DECIMAL(10,2) CHECK (distance_restaurant_delivery >= 0), -- in miles
    duration_restaurant_delivery DECIMAL(10,2) CHECK (duration_restaurant_delivery >= 0), -- in minutes
    
    -- Delivery verification
    delivery_code TEXT, -- Numeric code for delivery verification
    delivery_code_used BOOLEAN NOT NULL DEFAULT false,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_restaurant_id ON orders(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_delivery_user_id ON orders(delivery_user_id) WHERE delivery_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_orders_ready_for_delivery ON orders(status, delivery_user_id) WHERE status = 'ready' AND delivery_user_id IS NULL;

-- Advanced JSONB indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_orders_items_gin ON orders USING GIN (order_items);
CREATE INDEX IF NOT EXISTS idx_orders_address_gin ON orders USING GIN (delivery_address);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_orders_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_orders_updated_at();

-- Add comments
COMMENT ON TABLE orders IS 'Stores delivery-only orders with comprehensive tracking';
COMMENT ON COLUMN orders.order_items IS 'JSONB array of order items with details';
COMMENT ON COLUMN orders.delivery_address IS 'JSONB object with delivery address details';
COMMENT ON COLUMN orders.distance_restaurant_delivery IS 'Distance in miles from restaurant to delivery address';
COMMENT ON COLUMN orders.duration_restaurant_delivery IS 'Estimated duration in minutes from restaurant to delivery address';
COMMENT ON COLUMN orders.delivery_code IS 'Numeric code shown to customer for delivery verification';

