-- Migration: Add inventory and promo fields to menu_items table
-- Description: Extends menu_items with stock tracking and promotion metadata
-- Date: 2025-11-21

ALTER TABLE menu_items
ADD COLUMN IF NOT EXISTS stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
ADD COLUMN IF NOT EXISTS reorder_threshold INTEGER NOT NULL DEFAULT 10 CHECK (reorder_threshold >= 0),
ADD COLUMN IF NOT EXISTS reorder_quantity INTEGER NOT NULL DEFAULT 50 CHECK (reorder_quantity >= 0),
ADD COLUMN IF NOT EXISTS lead_time_days INTEGER NOT NULL DEFAULT 3 CHECK (lead_time_days >= 0),
ADD COLUMN IF NOT EXISTS is_promo BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS promo_note TEXT,
ADD COLUMN IF NOT EXISTS last_sales_7d INTEGER NOT NULL DEFAULT 0 CHECK (last_sales_7d >= 0),
ADD COLUMN IF NOT EXISTS last_sales_30d INTEGER NOT NULL DEFAULT 0 CHECK (last_sales_30d >= 0);

COMMENT ON COLUMN menu_items.stock_quantity IS 'Current on-hand stock quantity for this menu item';
COMMENT ON COLUMN menu_items.reorder_threshold IS 'When stock falls below this level, the item should be reordered';
COMMENT ON COLUMN menu_items.reorder_quantity IS 'Typical quantity to order when replenishing stock';
COMMENT ON COLUMN menu_items.lead_time_days IS 'Expected supplier lead time in days for replenishing this item';
COMMENT ON COLUMN menu_items.is_promo IS 'Whether this item is currently under a promotion';
COMMENT ON COLUMN menu_items.promo_note IS 'Short human-readable description of the promotion for this item';
COMMENT ON COLUMN menu_items.last_sales_7d IS 'Number of units sold in the last 7 days (for inventory analytics)';
COMMENT ON COLUMN menu_items.last_sales_30d IS 'Number of units sold in the last 30 days (for inventory analytics)';


