-- Seed data for menu_items to support inventory testing and demos
-- Safe to run multiple times: uses ON CONFLICT DO NOTHING on item_id

INSERT INTO menu_items (
    item_id, restaurant_id, item_name, description,
    is_available, image, price,
    quantity, reorder_threshold, reorder_quantity, lead_time_days,
    is_promo, promo_note, last_sales_7d, last_sales_30d
)
VALUES
    -- Low stock items (quantity below threshold)
    (101, 10, 'Large Fries', 'Salty fries with house seasoning', TRUE, NULL, 5.00,
     2, 10, 50, 3, FALSE, NULL, 5, 20),
    (102, 9, 'Caesar Salad', 'Fresh romaine lettuce with parmesan and caesar dressing', TRUE, NULL, 10.99,
     3, 12, 30, 2, FALSE, NULL, 4, 18),

    -- Normal items (healthy stock and sales)
    (103, 9, 'Margherita Pizza', 'Classic pizza with tomato sauce, mozzarella, and fresh basil', TRUE, NULL, 12.99,
     40, 10, 20, 3, FALSE, NULL, 15, 60),
    (104, 11, 'Butter Chicken', 'Butter chicken with a blend of South Asian spices', TRUE, NULL, 10.55,
     60, 15, 30, 5, FALSE, NULL, 20, 80),

    -- Overstock items (very high quantity vs 30d sales)
    (105, 11, 'Chicken Biryani', 'Traditional chicken biryani with authentic spices', TRUE, NULL, 10.50,
     200, 10, 40, 4, FALSE, NULL, 10, 30),
    (106, 14, 'Strawberry Banana Smoothie', 'Fresh in-house smoothie', TRUE, NULL, 10.00,
     150, 8, 25, 2, FALSE, NULL, 6, 20),

    -- Stagnant items (non-zero quantity, no sales in 30 days)
    (107, 15, 'Big Burger', 'Big tasty burger for a good price', TRUE, NULL, 15.00,
     25, 10, 20, 3, TRUE, 'Limited-time burger promo', 0, 0),
    (108, 10, 'McDouble', 'Double patty burger', TRUE, NULL, 10.00,
     30, 10, 20, 3, FALSE, NULL, 0, 0)
ON CONFLICT (item_id) DO NOTHING;


