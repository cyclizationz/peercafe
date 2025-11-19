-- Migration: Notes on spatial_ref_sys and additional setup
-- Description: Information about PostGIS spatial_ref_sys table and setup notes
-- Date: 2025-01-XX

-- ============================================================================
-- SPATIAL_REF_SYS TABLE
-- ============================================================================
-- The spatial_ref_sys table is automatically created by PostGIS extension.
-- It contains coordinate reference system (CRS) definitions and should NOT
-- be manually created or modified.
--
-- To verify PostGIS is installed and spatial_ref_sys exists:
--   SELECT COUNT(*) FROM spatial_ref_sys;
--
-- The table contains standard EPSG coordinate systems (e.g., EPSG:4326 for WGS84).
-- Our restaurants.location column uses SRID 4326 (WGS84).

-- ============================================================================
-- SETUP INSTRUCTIONS
-- ============================================================================

-- 1. Run migrations in order:
--    - 001_create_restaurants_table.sql
--    - 002_create_users_table.sql
--    - 003_create_menu_items_table.sql
--    - 004_create_orders_table.sql

-- 2. Verify tables were created:
--    SELECT table_name FROM information_schema.tables 
--    WHERE table_schema = 'public' 
--    AND table_name IN ('restaurants', 'users', 'menu_items', 'orders')
--    ORDER BY table_name;

-- 3. Verify PostGIS extension:
--    SELECT * FROM pg_extension WHERE extname = 'postgis';

-- 4. Verify spatial_ref_sys exists (should return count > 0):
--    SELECT COUNT(*) FROM spatial_ref_sys;

-- ============================================================================
-- USEFUL QUERIES
-- ============================================================================

-- Find restaurants by location text (use address field, not geography):
--   SELECT * FROM restaurants 
--   WHERE address ILIKE '%Downtown%';

-- Find restaurants within radius (using geography):
--   SELECT * FROM restaurants
--   WHERE ST_DWithin(
--       location::geography,
--       ST_MakePoint(-78.680415, 35.785558)::geography,
--       5000  -- 5km radius in meters
--   );

-- Update location geography from latitude/longitude:
--   UPDATE restaurants
--   SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
--   WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- ============================================================================
-- IMPORTANT NOTES
-- ============================================================================

-- 1. Location searches should use the 'address' VARCHAR field for text matching,
--    NOT the 'location' GEOGRAPHY field. The geography field is for spatial queries.

-- 2. The 'location' field can be populated from latitude/longitude using:
--    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography

-- 3. Always use SRID 4326 (WGS84) for geographic coordinates.

-- 4. The spatial_ref_sys table is read-only and managed by PostGIS.

