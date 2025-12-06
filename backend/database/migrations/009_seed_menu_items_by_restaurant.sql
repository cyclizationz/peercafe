-- Migration: Seed menu items for all restaurants
-- Description: Adds 5 menu items per restaurant matching cuisine type and price range
-- Price ranges: $ (~$5-15), $$ (~$10-25), $$$ (~$20-40), $$$$ (~$35-60+);
-- Date: 2025-12-06
-- Note: Sequence is reset to avoid item_id conflicts with existing items

-- Set sequence to start from 200 to avoid conflicts with existing items
-- This ensures new items get IDs starting from max(existing_ids) + 1 or 200, whichever is higher
-- Use pg_get_serial_sequence to get the correct sequence name dynamically
DO $$
DECLARE
    seq_name TEXT;
    max_id INTEGER;
    next_val INTEGER;
BEGIN
    -- Get the sequence name for the item_id column
    SELECT pg_get_serial_sequence('menu_items', 'item_id') INTO seq_name;
    
    -- If sequence exists, reset it
    IF seq_name IS NOT NULL THEN
        SELECT COALESCE(MAX(item_id), 0) INTO max_id FROM menu_items;
        next_val := GREATEST(200, max_id + 1);
        EXECUTE format('SELECT setval(%L, %s, false)', seq_name, next_val);
    END IF;
END $$;

-- Italian Restaurants ($$ and $$$);
-- Restaurant 16: Mario's Pizza ($$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(16, 'Margherita Pizza', 'Classic pizza with fresh mozzarella, basil, and tomato sauce', true, 14.99, 50, 10, 30, 2),
(16, 'Pepperoni Pizza', 'Traditional pepperoni pizza with mozzarella cheese', true, 16.99, 45, 10, 30, 2),
(16, 'Chicken Alfredo', 'Creamy alfredo pasta with grilled chicken', true, 18.99, 40, 10, 25, 3),
(16, 'Caesar Salad', 'Fresh romaine lettuce with caesar dressing and parmesan', true, 12.99, 60, 8, 20, 2),
(16, 'Garlic Bread', 'Fresh baked bread with garlic butter', true, 6.99, 80, 15, 40, 1);

-- Restaurant 13: La Bella Vita ($$$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(13, 'Osso Buco', 'Braised veal shanks with risotto milanese', true, 38.99, 20, 5, 15, 4),
(13, 'Lobster Ravioli', 'Homemade ravioli filled with lobster in cream sauce', true, 32.99, 25, 5, 20, 3),
(13, 'Truffle Risotto', 'Creamy arborio rice with black truffle', true, 28.99, 30, 8, 20, 3),
(13, 'Branzino', 'Mediterranean sea bass with lemon and herbs', true, 34.99, 22, 5, 18, 3),
(13, 'Tiramisu', 'Classic Italian dessert with espresso and mascarpone', true, 12.99, 40, 10, 25, 2);

-- American Restaurants ($ and $$ and $$$);
-- Restaurant 15: Burger Haven ($$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(15, 'Classic Cheeseburger', 'Angus beef patty with cheese, lettuce, tomato, and special sauce', true, 12.99, 60, 15, 40, 2),
(15, 'BBQ Bacon Burger', 'Beef patty with crispy bacon, cheddar, and BBQ sauce', true, 15.99, 50, 12, 35, 2),
(15, 'Crispy Chicken Sandwich', 'Breaded chicken breast with pickles and mayo', true, 11.99, 55, 12, 35, 2),
(15, 'Loaded Fries', 'French fries topped with cheese, bacon, and jalapeños', true, 8.99, 70, 20, 50, 1),
(15, 'Chocolate Milkshake', 'Rich chocolate milkshake with whipped cream', true, 6.99, 80, 25, 60, 1);

-- Restaurant 9: Port City Java ($)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(9, 'Americano', 'Espresso with hot water', true, 4.99, 100, 20, 60, 1),
(9, 'Cappuccino', 'Espresso with steamed milk and foam', true, 5.99, 90, 20, 60, 1),
(9, 'Blueberry Muffin', 'Fresh baked blueberry muffin', true, 3.99, 80, 25, 70, 1),
(9, 'Bagel with Cream Cheese', 'Fresh bagel with cream cheese', true, 4.99, 85, 20, 60, 1),
(9, 'Breakfast Sandwich', 'Egg, cheese, and bacon on English muffin', true, 6.99, 70, 15, 50, 1);

-- Restaurant 10: McDonalds ($)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(10, 'Big Mac', 'Two all-beef patties, special sauce, lettuce, cheese', true, 5.99, 200, 50, 150, 1),
(10, 'Quarter Pounder', 'Quarter pound beef patty with cheese', true, 6.49, 180, 45, 140, 1),
(10, 'Chicken McNuggets (10pc)', 'Breaded chicken nuggets with your choice of sauce', true, 7.99, 150, 40, 120, 1),
(10, 'French Fries (Large)', 'Golden crispy french fries', true, 3.99, 250, 60, 200, 1),
(10, 'Apple Pie', 'Hot apple pie dessert', true, 1.99, 100, 30, 80, 1);

-- Restaurant 30: The Urban Fork ($$$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(30, 'Wagyu Burger', 'Premium wagyu beef burger with truffle aioli', true, 28.99, 30, 8, 25, 3),
(30, 'Filet Mignon', '8oz prime filet with roasted vegetables', true, 42.99, 20, 5, 18, 4),
(30, 'Lobster Mac & Cheese', 'Creamy macaroni with fresh lobster', true, 32.99, 25, 6, 20, 3),
(30, 'Caesar Salad', 'Classic caesar with grilled chicken', true, 18.99, 40, 10, 30, 2),
(30, 'Chocolate Lava Cake', 'Warm chocolate cake with vanilla ice cream', true, 14.99, 35, 10, 25, 2);

-- Indian Restaurants ($$ and $$$);
-- Restaurant 36: Tandoori Flame ($$$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(36, 'Butter Chicken', 'Tender chicken in creamy tomato curry', true, 22.99, 40, 10, 30, 3),
(36, 'Lamb Vindaloo', 'Spicy lamb curry with potatoes', true, 24.99, 35, 8, 25, 3),
(36, 'Chicken Biryani', 'Fragrant basmati rice with spiced chicken', true, 20.99, 45, 12, 35, 3),
(36, 'Garlic Naan', 'Fresh baked naan with garlic and herbs', true, 5.99, 80, 20, 60, 1),
(36, 'Mango Lassi', 'Sweet yogurt drink with mango', true, 4.99, 70, 15, 50, 1);

-- Restaurant 11: Spice Route ($$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(11, 'Chicken Tikka Masala', 'Grilled chicken in creamy tomato sauce', true, 16.99, 50, 12, 40, 3),
(11, 'Vegetable Samosa', 'Crispy pastries filled with spiced vegetables', true, 6.99, 80, 20, 60, 2),
(11, 'Palak Paneer', 'Spinach curry with Indian cheese', true, 14.99, 45, 10, 35, 2),
(11, 'Basmati Rice', 'Steamed basmati rice', true, 4.99, 100, 30, 80, 1),
(11, 'Gulab Jamun', 'Sweet milk dumplings in syrup', true, 5.99, 60, 15, 45, 2);

-- Restaurant 28: The Curry Club ($$$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(28, 'Lamb Rogan Josh', 'Aromatic lamb curry with yogurt and spices', true, 26.99, 30, 8, 25, 3),
(28, 'Chicken Korma', 'Mild creamy curry with almonds', true, 22.99, 40, 10, 30, 3),
(28, 'Paneer Makhani', 'Indian cheese in rich tomato gravy', true, 18.99, 35, 8, 28, 2),
(28, 'Tandoori Mixed Grill', 'Assorted grilled meats and vegetables', true, 28.99, 25, 6, 20, 3),
(28, 'Kheer', 'Traditional rice pudding dessert', true, 6.99, 50, 12, 40, 2);

-- Chinese Restaurant ($);
-- Restaurant 33: Dragon Wok ($)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(33, 'General Tso''s Chicken', 'Crispy chicken in sweet and spicy sauce', true, 12.99, 60, 15, 45, 2),
(33, 'Beef Lo Mein', 'Stir-fried noodles with beef and vegetables', true, 11.99, 55, 12, 40, 2),
(33, 'Sweet and Sour Pork', 'Battered pork with bell peppers and pineapple', true, 10.99, 50, 12, 38, 2),
(33, 'Egg Rolls (2pc)', 'Crispy vegetable egg rolls', true, 5.99, 80, 20, 60, 1),
(33, 'Fried Rice', 'Wok-fried rice with vegetables and egg', true, 8.99, 70, 18, 55, 1);

-- Mediterranean Restaurant ($$);
-- Restaurant 35: Golden Falafel ($$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(35, 'Falafel Wrap', 'Crispy falafel with tahini, vegetables in pita', true, 10.99, 60, 15, 45, 2),
(35, 'Chicken Shawarma', 'Marinated chicken with garlic sauce in pita', true, 12.99, 55, 12, 40, 2),
(35, 'Hummus Plate', 'Creamy hummus with pita bread and vegetables', true, 9.99, 65, 15, 50, 2),
(35, 'Greek Salad', 'Fresh vegetables with feta and olives', true, 11.99, 50, 10, 35, 2),
(35, 'Baklava', 'Honey-soaked phyllo pastry with nuts', true, 6.99, 40, 10, 30, 2);

-- BBQ Restaurant ($$);
-- Restaurant 37: Blue Ridge BBQ ($$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(37, 'Pulled Pork Sandwich', 'Slow-smoked pulled pork with BBQ sauce', true, 13.99, 50, 12, 40, 3),
(37, 'BBQ Ribs (Half Rack)', 'Tender ribs with house BBQ sauce', true, 18.99, 35, 8, 28, 4),
(37, 'Brisket Plate', 'Sliced brisket with two sides', true, 19.99, 30, 8, 25, 4),
(37, 'Mac and Cheese', 'Creamy macaroni and cheese', true, 7.99, 60, 15, 45, 2),
(37, 'Cornbread', 'Fresh baked cornbread', true, 4.99, 70, 18, 55, 1);

-- Thai Restaurant ($$);
-- Restaurant 38: Thai Kitchen ($$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(38, 'Pad Thai', 'Stir-fried rice noodles with shrimp and peanuts', true, 15.99, 45, 10, 35, 2),
(38, 'Green Curry', 'Spicy green curry with chicken and vegetables', true, 16.99, 40, 10, 30, 2),
(38, 'Tom Yum Soup', 'Hot and sour soup with shrimp', true, 12.99, 50, 12, 40, 2),
(38, 'Spring Rolls (4pc)', 'Crispy vegetable spring rolls', true, 7.99, 60, 15, 50, 1),
(38, 'Mango Sticky Rice', 'Sweet sticky rice with fresh mango', true, 8.99, 35, 10, 30, 2);

-- Vegan Restaurant ($$);
-- Restaurant 14: Green Bowl ($$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(14, 'Quinoa Buddha Bowl', 'Quinoa with roasted vegetables, avocado, and tahini', true, 14.99, 50, 12, 40, 2),
(14, 'Vegan Burger', 'Plant-based patty with all the fixings', true, 13.99, 45, 10, 35, 2),
(14, 'Kale Caesar Salad', 'Kale salad with vegan caesar dressing', true, 12.99, 55, 12, 40, 2),
(14, 'Acai Bowl', 'Acai smoothie bowl with granola and fruits', true, 11.99, 40, 10, 30, 1),
(14, 'Vegan Chocolate Cake', 'Rich chocolate cake made without dairy', true, 8.99, 30, 8, 25, 2);

-- Seafood Restaurant ($$$$);
-- Restaurant 34: Seaside Grill ($$$$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(34, 'Lobster Thermidor', 'Lobster in creamy brandy sauce', true, 58.99, 15, 5, 12, 4),
(34, 'Grilled Salmon', 'Atlantic salmon with lemon butter and vegetables', true, 32.99, 30, 8, 25, 2),
(34, 'Seafood Paella', 'Spanish rice dish with mixed seafood', true, 42.99, 20, 6, 18, 3),
(34, 'Oysters (Half Dozen)', 'Fresh raw oysters with mignonette', true, 24.99, 25, 8, 20, 1),
(34, 'Key Lime Pie', 'Classic Florida key lime pie', true, 12.99, 35, 10, 28, 2);

-- Japanese Restaurants ($$$ and $$$$);
-- Restaurant 12: Sushi Harbor ($$$$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(12, 'Omakase Sashimi Platter', 'Chef''s selection of premium sashimi', true, 65.99, 12, 4, 10, 1),
(12, 'Dragon Roll', 'Eel, cucumber, avocado with eel sauce', true, 18.99, 30, 8, 25, 1),
(12, 'Chirashi Bowl', 'Assorted sashimi over sushi rice', true, 28.99, 25, 6, 20, 1),
(12, 'Miso Soup', 'Traditional Japanese soup with tofu', true, 4.99, 80, 20, 60, 1),
(12, 'Green Tea Ice Cream', 'Premium matcha ice cream', true, 8.99, 40, 10, 30, 2);

-- Restaurant 31: Sakura Garden ($$$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(31, 'Sashimi Deluxe', 'Assorted fresh sashimi (12 pieces)', true, 32.99, 25, 6, 20, 1),
(31, 'Teriyaki Chicken', 'Grilled chicken with teriyaki sauce and rice', true, 22.99, 40, 10, 30, 2),
(31, 'Tempura Udon', 'Hot udon noodles with tempura vegetables', true, 18.99, 35, 8, 28, 2),
(31, 'California Roll', 'Crab, avocado, cucumber roll', true, 8.99, 50, 12, 40, 1),
(31, 'Mochi Ice Cream', 'Japanese rice cake with ice cream', true, 7.99, 45, 12, 35, 2);

-- Creole Restaurant ($$);
-- Restaurant 39: Creole House ($$)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(39, 'Jambalaya', 'Spicy rice dish with sausage, chicken, and shrimp', true, 18.99, 35, 8, 28, 3),
(39, 'Gumbo', 'Rich stew with okra, seafood, and sausage', true, 16.99, 40, 10, 30, 3),
(39, 'Crawfish Étouffée', 'Crawfish in rich roux-based sauce', true, 22.99, 30, 8, 25, 3),
(39, 'Beignets', 'New Orleans style fried doughnuts', true, 7.99, 50, 12, 40, 1),
(39, 'Bananas Foster', 'Caramelized bananas with rum and ice cream', true, 12.99, 25, 8, 20, 2);

-- Sandwiches Restaurant ($);
-- Restaurant 29: Subway Avent Ferry ($)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(29, 'Italian BMT', 'Pepperoni, salami, and ham with vegetables', true, 8.99, 80, 20, 60, 1),
(29, 'Turkey Breast', 'Oven roasted turkey with your choice of veggies', true, 7.99, 85, 20, 65, 1),
(29, 'Veggie Delite', 'Fresh vegetables and cheese', true, 6.99, 90, 25, 70, 1),
(29, 'Chicken Teriyaki', 'Marinated chicken with teriyaki sauce', true, 8.49, 75, 18, 55, 1),
(29, 'Chocolate Chip Cookie', 'Fresh baked chocolate chip cookie', true, 1.99, 150, 40, 120, 1);

-- Farm-to-Table Restaurant ($);
-- Restaurant 32: Harvest Table ($)
INSERT INTO menu_items (restaurant_id, item_name, description, is_available, price, quantity, reorder_threshold, reorder_quantity, lead_time_days) VALUES
(32, 'Farm Fresh Salad', 'Mixed greens with seasonal vegetables and vinaigrette', true, 12.99, 50, 12, 40, 1),
(32, 'Grilled Chicken Sandwich', 'Local chicken with arugula and tomato on artisan bread', true, 11.99, 45, 10, 35, 2),
(32, 'Seasonal Vegetable Soup', 'Soup made with locally sourced vegetables', true, 8.99, 60, 15, 45, 1),
(32, 'Quiche of the Day', 'Daily quiche with seasonal ingredients', true, 10.99, 35, 8, 28, 2),
(32, 'Apple Crisp', 'Warm apple crisp with local honey and vanilla ice cream', true, 7.99, 40, 10, 30, 2);

