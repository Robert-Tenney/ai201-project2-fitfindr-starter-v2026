"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable
from mcp_client import call_tool, MCPError  # ← added: Milestone 1


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── parsing the query ─────────────────────────────────────────────────────────

_PRICE_WORDS = r"(?:under|below|less than|up to|at most|max(?:imum)?)"

# "under $30", "$30", "below 30" — the dollar sign is optional when a price
# word comes first. (In PowerShell, double quotes delete "$30", leaving
# "under " — no number, so no ceiling. Use single quotes.)
_PRICE_RE = re.compile(
    rf"(?:{_PRICE_WORDS}\s*)?\$\s*(\d+(?:\.\d+)?)|{_PRICE_WORDS}\s+(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)

# "size M", "in size M", "size 8", "size XXS"
_SIZE_RE = re.compile(r"\b(?:in\s+)?size\s+([A-Za-z0-9/.]+)", re.IGNORECASE)

_FILLER_RE = re.compile(
    r"\b(?:i'?m looking for|i am looking for|looking for|i want|i need|find me|show me)\b",
    re.IGNORECASE,
)


def _parse_query(query: str) -> dict:
    """
    Pull a description, a size and a max_price out of plain language, with regex.

    "designer ballgown size XXS under $5"
        -> {"description": "designer ballgown", "size": "XXS", "max_price": 5.0}

    A size or price that isn't in the query comes back as None, which tells
    search_listings to skip that filter.
    """
    size = None
    size_match = _SIZE_RE.search(query)
    if size_match:
        size = size_match.group(1).upper()

    max_price = None
    price_match = _PRICE_RE.search(query)
    if price_match:
        max_price = float(price_match.group(1) or price_match.group(2))

    rest = _SIZE_RE.sub(" ", query)
    rest = _PRICE_RE.sub(" ", rest)
    rest = _FILLER_RE.sub(" ", rest)
    description = re.sub(r"\s+", " ", rest).strip(" ,.;-")

    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Say what to change, using the filters that were actually applied."""
    searched = f"'{parsed['description']}'" if parsed["description"] else "that search"
    if parsed["size"]:
        searched += f" in size {parsed['size']}"
    if parsed["max_price"] is not None:
        searched += f" under ${parsed['max_price']:g}"

    tips = []
    if parsed["max_price"] is not None:
        tips.append(f"raise your price limit above ${parsed['max_price']:g}")
    if parsed["size"]:
        tips.append(f"drop or change the size ({parsed['size']})")
    tips.append("use fewer or broader keywords (for example 'dress' instead of a long description)")

    if len(tips) > 1:
        advice = ", ".join(tips[:-1]) + ", or " + tips[-1]
    else:
        advice = tips[0]
    return f"No listings matched {searched}. You could {advice}."


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Branch rule: after search_listings runs, if session["search_results"] is
    empty, set session["error"] to a message naming what to change, leave
    session["fit_card"] as None, and return without calling suggest_outfit.
    Otherwise take the first result and go on to suggest_outfit, then
    create_fit_card.

    Every value moves through the session: each step reads its input back out
    of it rather than receiving it straight from the previous call.

    Returns the session dict. Check session["error"] first.
    """
    session = new_session(query, wardrobe)

    step = "search"
    count = 0

    while step:
        count += 1
        trace.check_iterations(count)

        if step == "search":
            session["parsed"] = _parse_query(session["query"])
            parsed = session["parsed"]
            # Milestone 1: this was
            #   session["search_results"] = search_listings(
            #       parsed["description"], parsed["size"], parsed["max_price"]
            #   )
            # and now goes through the MCP server instead.
            try:
                session["search_results"] = call_tool("search_listings", {
                    "description": parsed["description"],
                    "size": parsed["size"],
                    "max_price": parsed["max_price"],
                })
            except MCPError as exc:
                session["error"] = f"The search service couldn't be reached. Try again. ({exc})"
                return session

            # ── THE BRANCH ────────────────────────────────────────────────
            if not session["search_results"]:
                session["error"] = _no_results_message(parsed)
                return session

            session["selected_item"] = session["search_results"][0]
            step = "suggest"

        elif step == "suggest":
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            step = "card"

        elif step == "card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            step = None

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )