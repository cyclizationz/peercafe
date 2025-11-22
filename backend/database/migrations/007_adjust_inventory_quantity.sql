-- Migration: Adjust inventory fields to use quantity as canonical stock
-- Description: Backfill quantity from stock_quantity (if needed) and drop stock_quantity column
-- Date: 2025-11-21

-- Optional backfill: if quantity is zero but stock_quantity has data, copy it over
UPDATE menu_items
SET quantity = stock_quantity
WHERE (quantity IS NULL OR quantity = 0)
  AND stock_quantity IS NOT NULL
  AND stock_quantity > 0;

-- Drop stock_quantity column now that quantity is canonical
ALTER TABLE menu_items
DROP COLUMN IF EXISTS stock_quantity;

-- Clarify quantity semantics
COMMENT ON COLUMN menu_items.quantity IS 'Available on-hand quantity for inventory tracking (0 = out of stock)';


