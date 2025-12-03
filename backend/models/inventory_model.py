from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    """Menu item with inventory-related fields."""

    item_id: int = Field(..., description="Unique identifier for the menu item")
    restaurant_id: int = Field(
        ..., description="ID of the restaurant this item belongs to"
    )
    item_name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the menu item"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Description of the menu item"
    )
    is_available: bool = Field(
        True, description="Whether the item is available for ordering"
    )
    image: Optional[str] = Field(None, description="URL to item image")
    price: float = Field(..., gt=0, description="Price of the item")

    # Inventory-specific fields (mirrors Supabase schema)
    quantity: int = Field(
        0, ge=0, description="Current on-hand stock quantity for this item"
    )
    reorder_threshold: int = Field(
        10,
        ge=0,
        description="When stock falls below this level, the item should be reordered",
    )
    reorder_quantity: int = Field(
        50,
        ge=0,
        description="Typical quantity to order when replenishing stock",
    )
    lead_time_days: int = Field(
        3,
        ge=0,
        description="Expected supplier lead time in days for replenishing this item",
    )
    is_promo: bool = Field(
        False, description="Whether this item is currently under a promotion"
    )
    promo_note: Optional[str] = Field(
        None, description="Short human-readable description of the promotion"
    )
    last_sales_7d: int = Field(
        0,
        ge=0,
        description="Number of units sold in the last 7 days (for analytics)",
    )
    last_sales_30d: int = Field(
        0,
        ge=0,
        description="Number of units sold in the last 30 days (for analytics)",
    )

    created_at: Optional[datetime] = Field(
        None, description="When the item was created"
    )
    updated_at: Optional[datetime] = Field(
        None, description="When the item was last updated"
    )


class LowStockItem(BaseModel):
    item: InventoryItem
    shortage: int = Field(
        ..., description="How many units below the reorder_threshold the item is"
    )


class OverstockItem(BaseModel):
    item: InventoryItem
    overstock_units: int = Field(
        ..., description="Approximate number of units considered excess stock"
    )


class StagnantItem(BaseModel):
    item: InventoryItem
    days_without_sales: int = Field(
        ..., description="Approximate number of days without meaningful sales"
    )


class InventorySnapshot(BaseModel):
    """Snapshot of current inventory state across menu items."""

    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When this snapshot was generated"
    )
    items: List[InventoryItem] = Field(
        default_factory=list, description="All inventory items included in the snapshot"
    )

    low_stock_items: List[LowStockItem] = Field(
        default_factory=list, description="Items currently below their reorder threshold"
    )
    overstock_items: List[OverstockItem] = Field(
        default_factory=list,
        description="Items considered overstocked based on sales and quantity",
    )
    stagnant_items: List[StagnantItem] = Field(
        default_factory=list,
        description="Items with very low or no sales in the recent period",
    )


class InventoryIssueSummary(BaseModel):
    """High-level summary of detected inventory issues."""

    total_items: int
    low_stock_count: int
    overstock_count: int
    stagnant_count: int


class RefillRecommendation(BaseModel):
    item: InventoryItem
    recommended_order_quantity: int
    rationale: str


class PromoSuggestion(BaseModel):
    item: InventoryItem
    suggestion: str
    priority: str = Field(
        "medium",
        description="Suggestion priority, e.g. 'low', 'medium', 'high'",
    )


class InventorySuggestions(BaseModel):
    """Structured container for different types of inventory suggestions."""

    summary: InventoryIssueSummary
    refill_recommendations: List[RefillRecommendation] = Field(default_factory=list)
    promo_suggestions: List[PromoSuggestion] = Field(default_factory=list)


