from typing import Optional

from fastapi import APIRouter, HTTPException, status

from database.supabase_db import create_supabase_client
from models.inventory_model import InventorySnapshot
from utils.inventory_analyzer import analyze_inventory, build_inventory_items
from utils.inventory_llm_advisor import InventoryLLMAdvisor

inventory_router = APIRouter()


supabase = create_supabase_client()


def get_supabase_client():
    global supabase
    if supabase is not None:
        return supabase
    supabase = create_supabase_client()
    return supabase


def _fetch_inventory_rows(restaurant_id: Optional[int] = None) -> list[dict]:
    client = get_supabase_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured.",
        )

    query = client.from_("menu_items").select(
        "item_id, restaurant_id, item_name, description, is_available, image, "
        "price, quantity, reorder_threshold, reorder_quantity, "
        "lead_time_days, is_promo, promo_note, last_sales_7d, last_sales_30d, "
        "created_at, updated_at"
    )
    if restaurant_id is not None:
        query = query.eq("restaurant_id", restaurant_id)

    result = query.execute()
    return result.data or []


@inventory_router.get("/inventory/status", response_model=InventorySnapshot)
async def get_inventory_status(restaurant_id: Optional[int] = None):
    """
    Return current inventory snapshot plus computed low-stock / overstock flags.
    """
    try:
        rows = _fetch_inventory_rows(restaurant_id)
        items = build_inventory_items(rows)
        snapshot = analyze_inventory(items)
        return snapshot
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching inventory status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch inventory status: {str(e)}"
        )


@inventory_router.post("/inventory/analysis")
async def inventory_analysis(restaurant_id: Optional[int] = None):
    """
    Use LLM to summarize inventory issues: low stock, overstock, and risks.
    """
    try:
        rows = _fetch_inventory_rows(restaurant_id)
        items = build_inventory_items(rows)
        snapshot = analyze_inventory(items)

        advisor = InventoryLLMAdvisor()
        analysis_text = advisor.generate_analysis(snapshot)

        return {
            "success": True,
            "analysis": analysis_text,
            "summary": {
                "total_items": len(snapshot.items),
                "low_stock_count": len(snapshot.low_stock_items),
                "overstock_count": len(snapshot.overstock_items),
                "stagnant_count": len(snapshot.stagnant_items),
            },
        }
    except ValueError as e:
        # Typically configuration error such as missing GROQ_API_KEY
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating inventory analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate inventory analysis: {str(e)}",
        )


@inventory_router.post("/inventory/refill-plan")
async def inventory_refill_plan(restaurant_id: Optional[int] = None):
    """
    Use LLM to generate a refill plan based on current inventory.
    """
    try:
        rows = _fetch_inventory_rows(restaurant_id)
        items = build_inventory_items(rows)
        snapshot = analyze_inventory(items)

        advisor = InventoryLLMAdvisor()
        plan_text = advisor.generate_refill_plan(snapshot)

        return {
            "success": True,
            "plan": plan_text,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating refill plan: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate refill plan: {str(e)}"
        )


@inventory_router.post("/inventory/promo-suggestions")
async def inventory_promo_suggestions(restaurant_id: Optional[int] = None):
    """
    Use LLM to suggest promotions for overstocked or stagnant items.
    """
    try:
        rows = _fetch_inventory_rows(restaurant_id)
        items = build_inventory_items(rows)
        snapshot = analyze_inventory(items)

        advisor = InventoryLLMAdvisor()
        suggestions_text = advisor.generate_promo_suggestions(snapshot)

        return {
            "success": True,
            "suggestions": suggestions_text,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating promo suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate promo suggestions: {str(e)}",
        )
