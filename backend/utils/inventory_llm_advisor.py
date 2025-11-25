import os
from typing import List

from dotenv import load_dotenv
from groq import Groq

from models.inventory_model import InventorySnapshot, InventorySuggestions


class InventoryLLMAdvisor:
    """LLM-backed advisor for inventory management decisions."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set in environment. "
                "Set it to enable inventory LLM advisor."
            )
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

    def _snapshot_to_context(self, snapshot: InventorySnapshot) -> str:
        """Render a compact textual representation of the inventory snapshot.

        Note: we deliberately omit raw IDs from the textual context so the
        model focuses on human-friendly names and business fields.
        """
        lines: List[str] = []
        for item in snapshot.items:
            lines.append(
                f"{item.item_name}: "
                f"price={item.price}, "
                f"stock={item.quantity}, "
                f"reorder_threshold={item.reorder_threshold}, "
                f"reorder_quantity={item.reorder_quantity}, "
                f"lead_time_days={item.lead_time_days}, "
                f"last_sales_7d={item.last_sales_7d}, "
                f"last_sales_30d={item.last_sales_30d}, "
                f"is_promo={item.is_promo}, "
                f"promo_note={item.promo_note or 'none'}"
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
            "You are an experienced restaurant inventory manager.\n\n"
            "Your goals:\n"
            "- Look at the inventory data provided and give practical advice.\n"
            "- Never reveal or mention any internal IDs, codes, or database keys.\n"
            "- Refer to items only by their names or clear descriptions.\n"
            "- For every suggestion you make, briefly explain WHY you are suggesting it.\n"
            "- Make it very clear that your suggestions are advisory only and must be\n"
            "  reviewed by a human before any financial or operational decisions are made.\n"
            "- Keep your language natural and conversational — like you’re briefing a colleague.\n"
            "- At the end of your answer, ask 1–2 short questions that invite the user\n"
            "  to refine or adjust the plan.\n\n"
            "Important safety rules:\n"
            "- You can be wrong. Explicitly remind the user to double-check your suggestions\n"
            "  against real sales data, supplier constraints, and company policies.\n"
            "- Do NOT present your output as guaranteed, final, or legally/financially binding."
        )
        user_prompt = (
            "Take a look at this inventory snapshot and tell me:\n\n"
            "1) Which items are running low or might run out soon?\n"
            "2) What are we overstocked on?\n"
            "3) What should we do about it right away?\n\n"
            "For each point, keep it brief and actionable, and explain your reasoning\n"
            "in plain language.\n\n"
            "Remember:\n"
            "- Do NOT show any internal IDs or codes in your answer.\n"
            "- Make it clear that this is advice that should be reviewed by a manager\n"
            "  before acting on it.\n\n"
            f"Inventory:\n{context}"
        )
        return self._call_llm(system_prompt, user_prompt)

    def generate_refill_plan(self, snapshot: InventorySnapshot) -> str:
        """Generate a refill plan as human-readable text."""
        context = self._snapshot_to_context(snapshot)
        system_prompt = (
            "You are helping plan restaurant restocking.\n\n"
            "Your goals:\n"
            "- Give straightforward advice on what to order and when.\n"
            "- Never show internal IDs, codes, or database keys in your answer.\n"
            "- Base your suggestions on stock, reorder_threshold, reorder_quantity,\n"
            "  lead_time_days, and recent sales.\n"
            "- For each item you recommend ordering, briefly explain WHY (for example:\n"
            "  'stock is below threshold and lead time is 3 days, so we should order now').\n"
            "- Group suggestions by restaurant in a way that is easy to scan and act on.\n"
            "- Clearly state that this is an AI-generated plan that must be checked by a\n"
            "  human before any purchase orders are placed.\n"
            "- End with 1–2 simple follow-up questions inviting the user to refine the plan.\n\n"
            "Important safety rules:\n"
            "- You can be wrong. Remind the user to verify quantities, prices, and supplier\n"
            "  constraints before ordering.\n"
            "- Avoid any language that sounds like a guarantee or mandatory instruction;\n"
            "  present it as informed advice."
        )
        user_prompt = (
            "Based on this inventory data, help me figure out what we need to restock:\n\n"
            "- Look for items below their reorder_threshold.\n"
            "- Use reorder_quantity and lead_time_days to suggest how much to order and when.\n"
            "- Group your suggestions by restaurant and keep them clear and concise.\n"
            "- For each suggestion, explain your reasoning in simple terms.\n\n"
            "Do NOT show any internal IDs or codes. Treat this as an advisory plan that\n"
            "a manager will review before making any purchases.\n\n"
            f"Inventory:\n{context}"
        )
        return self._call_llm(system_prompt, user_prompt)

    def generate_promo_suggestions(self, snapshot: InventorySnapshot) -> str:
        """Generate promo suggestions for overstocked or stagnant items."""
        context = self._snapshot_to_context(snapshot)
        system_prompt = (
            "You are a restaurant marketing strategist suggesting promotions.\n\n"
            "Your goals:\n"
            "- Propose realistic, simple promotions that could plausibly be implemented.\n"
            "- Focus on items with high stock relative to recent sales or items that are\n"
            "  not selling well.\n"
            "- Never show internal IDs, codes, or database keys in your answer.\n"
            "- For each promo idea, give a quick explanation of WHY it makes sense\n"
            "  (for example: high stock and low recent sales).\n"
            "- Use friendly, enthusiastic language, like you’re pitching ideas in a meeting.\n"
            "- Clearly remind the user that these are suggestions only and that they must\n"
            "  check them against brand guidelines, legal rules, and financial targets.\n"
            "- End with 1–2 simple follow-up questions that invite the user to adjust or\n"
            "  narrow down the promo plan.\n\n"
            "Important safety rules:\n"
            "- You can be wrong or incomplete; explicitly say that managers should review\n"
            "  and adapt ideas before launching any campaign.\n"
            "- Avoid promising specific financial outcomes or guarantees."
        )
        user_prompt = (
            "Looking at our current inventory, what promotions should we run?\n\n"
            "Focus on:\n"
            "- Items we have too much of.\n"
            "- Things that aren't selling well lately.\n\n"
            "Give me 3–7 solid promo ideas. For each idea:\n"
            "- Make it practical and appealing to customers.\n"
            "- Briefly explain why this promo fits the current inventory situation.\n\n"
            "Do NOT reveal any internal IDs or codes. Make it clear these are suggestions\n"
            "that must be reviewed and approved before launch.\n\n"
            f"Inventory:\n{context}"
        )
        return self._call_llm(system_prompt, user_prompt)


__all__ = ["InventoryLLMAdvisor"]


