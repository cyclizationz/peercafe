from unittest.mock import MagicMock, patch

import pytest

from models.inventory_model import InventoryItem, InventorySnapshot
from utils.inventory_llm_advisor import InventoryLLMAdvisor


def _sample_snapshot() -> InventorySnapshot:
    item = InventoryItem(
        item_id=1,
        restaurant_id=1,
        item_name="Test Item",
        description="Tasty",
        is_available=True,
        image=None,
        price=10.0,
        quantity=5,
        reorder_threshold=10,
        reorder_quantity=20,
        lead_time_days=3,
        is_promo=False,
        promo_note=None,
        last_sales_7d=1,
        last_sales_30d=2,
    )
    return InventorySnapshot(
        items=[item],
        low_stock_items=[],
        overstock_items=[],
        stagnant_items=[],
    )


@patch("utils.inventory_llm_advisor.Groq")
def test_inventory_llm_advisor_calls_groq(mock_groq):
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="ok"))]
    )

    with patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}):
        advisor = InventoryLLMAdvisor()

    snapshot = _sample_snapshot()

    advisor.generate_analysis(snapshot)
    advisor.generate_refill_plan(snapshot)
    advisor.generate_promo_suggestions(snapshot)

    assert mock_client.chat.completions.create.call_count == 3


def test_inventory_llm_advisor_missing_key_raises():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            InventoryLLMAdvisor()
