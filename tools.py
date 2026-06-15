"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    # ... (all the docstring) ...
    listings = load_listings()

    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]
    if size is not None:
        listings = [l for l in listings if size.upper() in l["size"].upper()]

    keywords = description.lower().split()
    def score(listing):
        text = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            " ".join(listing.get("style_tags", [])),
        ]).lower()
        return sum(1 for kw in keywords if kw in text)

    scored = [(score(l), l) for l in listings]
    return [l for s, l in sorted(scored, key=lambda x: -x[0]) if s > 0]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    client = _get_groq_client()

    item_description = (
        f"{new_item.get('title')} — {new_item.get('category')}, "
        f"style: {', '.join(new_item.get('style_tags', []))}, "
        f"colors: {', '.join(new_item.get('colors', []))}"
    )

    if not wardrobe.get("items"):
        prompt = (
            f"A user just thrifted this item: {item_description}. "
            "They have no wardrobe saved yet. Give them 1-2 general styling tips — "
            "what kinds of pieces pair well with it and what vibe it suits."
        )
    else:
        wardrobe_text = "\n".join(
            f"- {item.get('name', 'Unknown')}: {item.get('category', '')}, "
            f"{item.get('color', '')}, {item.get('style', '')}"
            for item in wardrobe["items"]
        )
        prompt = (
            f"A user just thrifted this item: {item_description}.\n"
            f"Their wardrobe includes:\n{wardrobe_text}\n"
            "Suggest 1-2 specific outfit combinations using the new item and named pieces from their wardrobe."
        )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    if not outfit or not outfit.strip():
        return "Fit card unavailable: no outfit suggestion was provided."

    client = _get_groq_client()

    prompt = (
        f"Write a 2-4 sentence Instagram/TikTok caption for this thrifted outfit.\n"
        f"Item: {new_item.get('title')} — ${new_item.get('price')} from {new_item.get('platform')}\n"
        f"Outfit: {outfit}\n\n"
        "Make it sound casual and authentic, like a real OOTD post. "
        "Mention the item name, price, and platform naturally (once each). "
        "Be specific about the vibe. Do NOT sound like a product description."
    )

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.9,
)
    return response.choices[0].message.content