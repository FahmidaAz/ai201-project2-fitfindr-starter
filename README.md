# FitFindr

A thrift-shopping agent that finds secondhand clothing, suggests outfits, and generates a shareable fit card — all from a single natural language query.

## How to Run

```bash
pip install -r requirements.txt
# Add GROQ_API_KEY=your_key to a .env file
python app.py
```
Open http://localhost:7860 in your browser.

## Tools

**search_listings(description: str, size: str | None, max_price: float | None) → list[dict]**
Searches the mock listings dataset by keyword relevance. Filters by size and price if provided. Returns a list of matching listing dicts (fields: id, title, description, category, style_tags, size, condition, price, colors, brand, platform) sorted by relevance score. Returns an empty list if nothing matches.

**suggest_outfit(new_item: dict, wardrobe: dict) → str**
Given a thrifted item and the user's wardrobe, uses an LLM to suggest 1–2 outfit combinations. If the wardrobe is empty, returns general styling advice instead of specific combinations.

**create_fit_card(outfit: str, new_item: dict) → str**
Generates a 2–4 sentence casual caption for the outfit, styled like an Instagram OOTD post. Mentions the item name, price, and platform once each. Guards against empty outfit input.

## Planning Loop

The agent runs a linear conditional loop:
1. Parse the query for description, size, and max_price using regex
2. Call search_listings — if results are empty, set an error message and return early without calling the other tools
3. Select the top result and call suggest_outfit
4. Pass the outfit suggestion to create_fit_card
5. Return the completed session

The key decision point is step 2 — the agent only proceeds to outfit suggestion if a listing was found.

## State Management

All state lives in a session dict initialized at the start of each run. Each tool's output is stored in the session before being passed to the next tool: `search_results → selected_item → outfit_suggestion → fit_card`. No tool modifies the session directly — `run_agent()` handles all state writes.

## Error Handling

| Tool | Failure | Response |
|------|---------|----------|
| search_listings | No results | Sets session["error"]: "No listings found. Try removing the size filter or raising your price limit." Agent returns early. |
| suggest_outfit | Empty wardrobe | Falls back to general styling advice via LLM. Always returns a non-empty string. |
| create_fit_card | Empty outfit string | Returns "Fit card unavailable: no outfit suggestion was provided." No exception raised. |

**Triggered example:** Running `create_fit_card('', item)` returns the error string immediately without calling the LLM.

## AI Usage

**Tool implementation:** I gave Claude the Tool 1 spec block from planning.md (inputs, return value, failure mode) and asked it to implement `search_listings()` using `load_listings()`. I reviewed the generated code to confirm it filtered by all three parameters and handled the empty-results case, then tested it against 3 queries before trusting it.

**Planning loop:** I gave Claude the architecture diagram and Planning Loop + State Management sections from planning.md and asked it to implement `run_agent()`. I verified the generated code branched on the `search_listings` result and did not call all three tools unconditionally.

## Spec Reflection

The planning.md spec was accurate for all three tools and the planning loop. One thing I adjusted during implementation: `create_fit_card` used temperature 1.2 initially, which caused the LLM to return empty strings. Lowering it to 0.9 fixed the issue — the spec should have specified a concrete temperature value rather than just "higher temperature."
