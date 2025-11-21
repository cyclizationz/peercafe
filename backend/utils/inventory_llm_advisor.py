import os
from typing import List

from dotenv import load_dotenv
from groq import Groq

from models.inventory_model import InventorySnapshot, InventorySuggestions


class InventoryLLMAdvisor:
    """LLM-backed advisor for inventory management decisions."""

    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set in environment. "
                "Set it to enable inventory LLM advisor."
            )
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

    def _snapshot_to_context(self, snapshot: InventorySnapshot) -> str:
        """Render a compact textual representation of the inventory snapshot."""
        lines: List[str] = []
        for item in snapshot.items:
            lines.append(
                f"- {item.item_name} (id={item.item_id}, restaurant_id={item.restaurant_id}): "
                f"price={item.price}, stock={item.stock_quantity}, "
                f"reorder_threshold={item.reorder_threshold}, "
                f"reorder_quantity={item.reorder_quantity}, "
                f"lead_time_days={item.lead_time_days}, "
                f"last_sales_7d={item.last_sales_7d}, "
                f"last_sales_30d={item.last_sales_30d}, "
                f"is_promo={item.is_promo}, promo_note={item.promo_note or 'none'}"
            )
        return "\n".join(lines)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content or ""

    def generate_analysis(self, snapshot: InventorySnapshot) -> str:
        """High-level textual analysis of inventory issues."""
        context = self._snapshot_to_context(snapshot)
        system_prompt = (
            "You are an expert restaurant inventory planner. "
            "You must only reason about the items provided. "
            "Be concise and actionable."
        )
        user_prompt = (
            "Given the following inventory snapshot, identify:\n"
            "1) Items at risk of stockout or already insufficient.\n"
            "2) Items that appear overstocked.\n"
            "3) Key risks and recommended immediate actions.\n\n"
            f"Inventory:\n{context}"
        )
        return self._call_llm(system_prompt, user_prompt)

    def generate_refill_plan(self, snapshot: InventorySnapshot) -> str:
        """Generate a refill plan as human-readable text."""
        context = self._snapshot_to_context(snapshot)
        system_prompt = (
            "You are an operations planner for a food delivery platform. "
            "Your goal is to create a practical restocking plan."
        )
        user_prompt = (
            "Using the inventory data below, propose a restocking plan.\n"
            "- Focus on items below their reorder_threshold.\n"
            "- Use reorder_quantity and lead_time_days when suggesting order quantities and timing.\n"
            "- Keep the answer in short bullet points grouped by restaurant.\n\n"
            f"Inventory:\n{context}"
        )
        return self._call_llm(system_prompt, user_prompt)

    def generate_promo_suggestions(self, snapshot: InventorySnapshot) -> str:
        """Generate promo suggestions for overstocked or stagnant items."""
        context = self._snapshot_to_context(snapshot)
        system_prompt = (
            "You are a restaurant revenue manager focused on promotions and pricing. "
            "Your job is to suggest simple, realistic promotions."
        )
        user_prompt = (
            "Based on the inventory snapshot, suggest promotions for:\n"
            "- Overstocked items\n"
            "- Stagnant items with low recent sales\n"
            "Provide 3–7 concise promo ideas with clear reasoning.\n\n"
            f"Inventory:\n{context}"
        )
        return self._call_llm(system_prompt, user_prompt)


__all__ = ["InventoryLLMAdvisor"]


