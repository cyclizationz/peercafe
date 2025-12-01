from utils.inventory_analyzer import build_inventory_items, analyze_inventory


def test_build_inventory_items_and_analyze():
    rows = [
        {
            "item_id": 1,
            "restaurant_id": 1,
            "item_name": "Low Stock Item",
            "price": 10.0,
            "quantity": 2,
            "reorder_threshold": 5,
            "reorder_quantity": 10,
            "lead_time_days": 2,
            "is_promo": False,
            "promo_note": None,
            "last_sales_7d": 1,
            "last_sales_30d": 2,
        },
        {
            "item_id": 2,
            "restaurant_id": 1,
            "item_name": "Overstock Item",
            "price": 5.0,
            "quantity": 100,
            "reorder_threshold": 5,
            "reorder_quantity": 10,
            "lead_time_days": 2,
            "is_promo": False,
            "promo_note": None,
            "last_sales_7d": 1,
            "last_sales_30d": 10,
        },
        {
            "item_id": 3,
            "restaurant_id": 1,
            "item_name": "Stagnant Item",
            "price": 8.0,
            "quantity": 15,
            "reorder_threshold": 5,
            "reorder_quantity": 10,
            "lead_time_days": 2,
            "is_promo": False,
            "promo_note": None,
            "last_sales_7d": 0,
            "last_sales_30d": 0,
        },
    ]

    items = build_inventory_items(rows)
    assert len(items) == 3
    assert items[0].item_name == "Low Stock Item"

    snapshot = analyze_inventory(items)
    assert len(snapshot.low_stock_items) == 1
    assert snapshot.low_stock_items[0].item.item_id == 1
    assert len(snapshot.overstock_items) == 1
    assert snapshot.overstock_items[0].item.item_id == 2
    assert len(snapshot.stagnant_items) == 1
    assert snapshot.stagnant_items[0].item.item_id == 3


