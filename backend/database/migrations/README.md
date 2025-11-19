# Database Migrations

This directory contains SQL migration scripts for creating and managing the PeerCafe database schema.

## Purpose

- Store SQL migration scripts for database schema changes
- Backup database schema definitions
- Document database structure and changes over time
- Provide step-by-step setup instructions

## Migration Files

### 001_create_restaurants_table.sql
Creates the `restaurants` table with:
- Basic restaurant information (name, description, address, contact info)
- PostGIS geography support for spatial queries
- Latitude/longitude fields for coordinate storage
- Indexes for common queries

**Key Fields:**
- `location` (GEOGRAPHY) - PostGIS geography type for spatial queries
- `address` (VARCHAR) - Full address string for text-based searches
- `latitude`/`longitude` (DOUBLE PRECISION) - Coordinate values

**Important:** Location searches should use the `address` field for text pattern matching, not the `geography` type `location` field.

### 002_create_users_table.sql
Creates the `users` table for customer and delivery user accounts with:
- User authentication fields (email, password)
- Profile information (name, phone)
- Address fields for delivery
- Location coordinates

### 003_create_menu_items_table.sql
Creates the `menu_items` table for restaurant menu items with:
- Item details (name, description, price)
- Availability tracking
- Inventory quantity

### 004_create_orders_table.sql
Creates the `orders` table for delivery-only orders with:
- Order items stored as JSONB
- Delivery address stored as JSONB
- Status tracking with state machine
- Distance and duration calculations
- Delivery code verification

### 005_notes_and_spatial_ref_sys.sql
Documentation and notes about:
- PostGIS `spatial_ref_sys` table (auto-created, do not modify)
- Setup instructions
- Useful queries
- Important notes about geography vs address fields

## Setup Instructions

### Prerequisites
- PostgreSQL database (Supabase uses PostgreSQL)
- PostGIS extension enabled (for geography support)

### Running Migrations

1. **Connect to your Supabase database** via SQL Editor or psql

2. **Run migrations in order:**
   ```sql
   -- Run each migration file in sequence
   \i 001_create_restaurants_table.sql
   \i 002_create_users_table.sql
   \i 003_create_menu_items_table.sql
   \i 004_create_orders_table.sql
   ```

3. **Verify setup:**
   ```sql
   -- Check tables exist
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('restaurants', 'users', 'menu_items', 'orders')
   ORDER BY table_name;
   
   -- Check PostGIS extension
   SELECT * FROM pg_extension WHERE extname = 'postgis';
   
   -- Check spatial_ref_sys (should return count > 0)
   SELECT COUNT(*) FROM spatial_ref_sys;
   ```

## Important Notes

### Location Searches
- **Use `address` field** for text-based location searches (e.g., "Downtown", "Raleigh")
- **Use `location` geography field** for spatial queries (e.g., "within 5km radius")
- The `location` field can be populated from `latitude`/`longitude` using PostGIS functions

### Spatial Reference System
- The `spatial_ref_sys` table is automatically created by PostGIS
- **Do NOT manually create or modify** this table
- It contains standard coordinate reference system definitions (EPSG codes)
- Our schema uses SRID 4326 (WGS84) for geographic coordinates

### Foreign Key Relationships
- `menu_items.restaurant_id` → `restaurants.restaurant_id`
- `orders.user_id` → `users.user_id`
- `orders.delivery_user_id` → `users.user_id`
- `orders.restaurant_id` → `restaurants.restaurant_id`

## Schema Overview

```
restaurants (1) ──< (many) menu_items
restaurants (1) ──< (many) orders
users (1) ──< (many) orders (as customer)
users (1) ──< (many) orders (as delivery_user)
```

## Useful Queries

See `005_notes_and_spatial_ref_sys.sql` for example queries including:
- Text-based location searches
- Spatial queries using geography
- Updating geography from coordinates
- Finding restaurants within radius
