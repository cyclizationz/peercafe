from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from models.inventory_model import (
    InventoryIssueSummary,
    InventoryItem,
    InventorySnapshot,
    LowStockItem,
    OverstockItem,
    StagnantItem,
)


def build_inventory_items(rows: Iterable[dict]) -> List[InventoryItem]:
    """Convert raw Supabase rows into InventoryItem models."""
    items: List[InventoryItem] = []
    for row in rows:
        if not row:
            continue

        # Map DB column names to model fields with sensible fallbacks
        item = InventoryItem(
            item_id=row["item_id"],
            restaurant_id=row["restaurant_id"],
            item_name=row.get("item_name") or "",
            description=row.get("description"),
            is_available=row.get("is_available", True),
            image=row.get("image"),
            price=float(row.get("price", 0)),
            quantity=row.get("quantity", 0) or 0,
            reorder_threshold=row.get("reorder_threshold", 10),
            reorder_quantity=row.get("reorder_quantity", 50),
            lead_time_days=row.get("lead_time_days", 3),
            is_promo=row.get("is_promo", False),
            promo_note=row.get("promo_note"),
            last_sales_7d=row.get("last_sales_7d", 0),
            last_sales_30d=row.get("last_sales_30d", 0),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
        items.append(item)
    return items


def analyze_inventory(items: List[InventoryItem]) -> InventorySnapshot:
    """Compute low-stock, overstock, and stagnant items from a list of inventory items."""
    low_stock: List[LowStockItem] = []
    overstock: List[OverstockItem] = []
    stagnant: List[StagnantItem] = []

    for item in items:
        # Low stock: stock below threshold
        if item.quantity < item.reorder_threshold:
            shortage = item.reorder_threshold - item.quantity
            low_stock.append(LowStockItem(item=item, shortage=shortage))

        # Overstock: significantly more stock than needed based on 30 day sales.
        # Simple heuristic: if quantity > 2 * max(last_sales_30d, reorder_quantity)
        reference_demand = max(item.last_sales_30d, item.reorder_quantity, 1)
        if item.quantity > 2 * reference_demand:
            overstock_units = item.quantity - 2 * reference_demand
            overstock.append(OverstockItem(item=item, overstock_units=overstock_units))

        # Stagnant: very low recent sales relative to stock
        if item.quantity > 0 and item.last_sales_30d == 0:
            stagnant.append(
                StagnantItem(
                    item=item,
                    # With only aggregated counters we approximate stagnation in days
                    days_without_sales=30,
                )
            )

    summary = InventoryIssueSummary(
        total_items=len(items),
        low_stock_count=len(low_stock),
        overstock_count=len(overstock),
        stagnant_count=len(stagnant),
    )

    return InventorySnapshot(
        generated_at=datetime.utcnow(),
        items=items,
        low_stock_items=low_stock,
        overstock_items=overstock,
        stagnant_items=stagnant,
    )


__all__ = ["build_inventory_items", "analyze_inventory"]


