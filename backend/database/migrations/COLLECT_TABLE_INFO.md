# How to Collect Table Information from Supabase

This guide provides SQL queries to inspect existing table structures in your Supabase database.

## Quick Table Inspection

### 1. List All Tables
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

### 2. Get Table Structure (Columns, Types, Constraints)

#### For restaurants table:
```sql
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'restaurants'
ORDER BY ordinal_position;
```

#### For menu_items table:
```sql
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'menu_items'
ORDER BY ordinal_position;
```

#### For orders table:
```sql
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'orders'
ORDER BY ordinal_position;
```

#### For users table:
```sql
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'users'
ORDER BY ordinal_position;
```

### 3. Get Foreign Key Constraints
```sql
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND tc.table_schema = 'public';
```

### 4. Get Indexes
```sql
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

### 5. Get Check Constraints
```sql
SELECT
    tc.table_name,
    tc.constraint_name,
    cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc
  ON tc.constraint_name = cc.constraint_name
WHERE tc.constraint_type = 'CHECK'
AND tc.table_schema = 'public';
```

### 6. Get Triggers
```sql
SELECT
    trigger_name,
    event_object_table,
    action_statement,
    action_timing,
    event_manipulation
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;
```

## Complete Table DDL Export

### Export Full CREATE TABLE Statement
```sql
-- For PostgreSQL, use pg_dump or:
SELECT 
    'CREATE TABLE ' || table_name || ' (' || E'\n' ||
    string_agg(
        '    ' || column_name || ' ' || 
        CASE 
            WHEN data_type = 'character varying' THEN 'VARCHAR(' || character_maximum_length || ')'
            WHEN data_type = 'character' THEN 'CHAR(' || character_maximum_length || ')'
            WHEN data_type = 'numeric' THEN 'NUMERIC(' || numeric_precision || ',' || numeric_scale || ')'
            WHEN data_type = 'double precision' THEN 'DOUBLE PRECISION'
            ELSE UPPER(data_type)
        END ||
        CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
        CASE WHEN column_default IS NOT NULL THEN ' DEFAULT ' || column_default ELSE '' END,
        ',' || E'\n'
        ORDER BY ordinal_position
    ) || E'\n' || ');'
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'restaurants'  -- Change table name as needed
GROUP BY table_name;
```

## Sample Data Inspection

### Get Sample Rows
```sql
-- Restaurants
SELECT * FROM restaurants LIMIT 5;

-- Menu Items
SELECT * FROM menu_items LIMIT 5;

-- Orders
SELECT * FROM orders LIMIT 5;

-- Users (be careful with passwords!)
SELECT user_id, first_name, last_name, email, phone, is_admin, is_active 
FROM users LIMIT 5;
```

### Get Column Statistics
```sql
-- For restaurants table
SELECT 
    column_name,
    data_type,
    COUNT(*) as row_count,
    COUNT(DISTINCT column_name) as distinct_values
FROM restaurants, 
LATERAL jsonb_each_text(to_jsonb(restaurants))
GROUP BY column_name, data_type;
```

## PostGIS/Geography Specific Queries

### Check PostGIS Extension
```sql
SELECT * FROM pg_extension WHERE extname = 'postgis';
```

### Check Geography Columns
```sql
SELECT
    f_table_name as table_name,
    f_geography_column as column_name,
    coord_dimension,
    srid,
    type
FROM geography_columns
WHERE f_table_schema = 'public';
```

### Check spatial_ref_sys
```sql
-- Count of coordinate systems
SELECT COUNT(*) FROM spatial_ref_sys;

-- Common coordinate systems
SELECT srid, auth_name, auth_srid, proj4text
FROM spatial_ref_sys
WHERE auth_name = 'EPSG'
AND auth_srid IN (4326, 3857, 4269)
ORDER BY auth_srid;
```

## Using Supabase Dashboard

1. **Go to Table Editor:**
   - Navigate to your Supabase project
   - Click on "Table Editor" in the sidebar
   - Select the table you want to inspect

2. **View Table Structure:**
   - Click on the table name
   - View columns, types, and constraints in the UI
   - Check "Relationships" tab for foreign keys

3. **SQL Editor:**
   - Go to "SQL Editor"
   - Run the queries above to get detailed information
   - Use "New Query" to write custom queries

## Exporting Schema

### Using pg_dump (Command Line)
```bash
# Export schema only (no data)
pg_dump -h <host> -U <user> -d <database> --schema-only > schema.sql

# Export specific table
pg_dump -h <host> -U <user> -d <database> -t restaurants > restaurants.sql

# Export with data
pg_dump -h <host> -U <user> -d <database> > full_backup.sql
```

### Using Supabase CLI
```bash
# Install Supabase CLI first
npm install -g supabase

# Link to your project
supabase link --project-ref <your-project-ref>

# Generate migration from existing database
supabase db diff -f <migration_name>
```

## Notes

- The `spatial_ref_sys` table is managed by PostGIS and should not be manually modified
- Always backup your database before making schema changes
- Use transactions when testing schema modifications:
  ```sql
  BEGIN;
  -- Your changes here
  ROLLBACK; -- or COMMIT;
  ```

