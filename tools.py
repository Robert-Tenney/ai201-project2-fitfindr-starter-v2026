"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── helpers ───────────────────────────────────────────────────────────────────

# Words in a query that say nothing about the item. Without this, "a" or "in"
# would score a point on almost every listing.
_STOPWORDS = {
    "a", "an", "the", "for", "in", "of", "on", "to", "and", "or", "with",
    "i", "me", "my", "im", "want", "looking", "find", "need", "some", "any",
    "under", "over", "below", "less", "than", "size", "like", "something",
}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text).lower())


def _stem(word: str) -> str:
    """Crude plural handling so "tees" matches "tee" and "jeans" matches "jean"."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _keywords(description: str) -> set[str]:
    return {_stem(w) for w in _words(description) if w not in _STOPWORDS}


def _size_matches(listing_size, wanted: str) -> bool:
    """
    True when `wanted` equals one whole token of the listing's size.

    Tokens are split on "/", spaces, commas and hyphens, so "M" matches "S/M"
    but not "us 9", and "S" does not match "XS" or "XL". A multi-word request
    such as "us 9" also matches if it equals the whole size string.
    """
    wanted = str(wanted).strip().lower()
    if not wanted:
        return True
    listing_size = str(listing_size).strip().lower()
    tokens = {t for t in re.split(r"[\s/,\-]+", listing_size) if t}
    return wanted in tokens or wanted == listing_size


def _price_text(price) -> str:
    """24.0 -> "$24", 24.5 -> "$24.50". Used so the fit card shows a clean price."""
    try:
        price = float(price)
    except (TypeError, ValueError):
        return str(price)
    return f"${int(price)}" if price == int(price) else f"${price:.2f}"


def _describe(item: dict) -> str:
    """One readable line for a listing or wardrobe item, skipping empty fields."""
    parts = []
    for key, value in item.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        parts.append(f"{key}: {value}")
    return "; ".join(parts)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    Args:
        description: keywords describing what the user wants.
        size:        a size to filter by, or None to skip. Matches one whole
                     token of the listing's size, case-insensitively.
        max_price:   maximum price, inclusive, or None to skip.

    Returns:
        A list of matching listing dicts, best match first, at most
        config.SEARCH_RESULT_LIMIT of them. An empty list when nothing matches
        — never None, never an exception.
    """
    keywords = _keywords(description or "")
    scored = []

    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _size_matches(listing.get("size"), size):
            continue

        title_words = {_stem(w) for w in _words(listing.get("title", ""))}
        other_text = " ".join(
            [
                str(listing.get("description") or ""),
                str(listing.get("category") or ""),
                " ".join(str(t) for t in listing.get("style_tags") or []),
                " ".join(str(c) for c in listing.get("colors") or []),
                str(listing.get("brand") or ""),  # brand is often None
            ]
        )
        other_words = {_stem(w) for w in _words(other_text)}

        score = 0
        for word in keywords:
            if word in title_words:
                score += 2          # a title match counts double
            elif word in other_words:
                score += 1

        if score > 0:
            scored.append((score, listing))

    # sorted() is stable, so ties keep their order in the data file.
    scored.sort(key=lambda pair: -pair[0])
    return [listing for _, listing in scored][: config.SEARCH_RESULT_LIMIT]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    Args:
        new_item: a listing dict.
        wardrobe: a wardrobe dict with an 'items' key. May be empty.

    Returns:
        A non-empty string. With an empty wardrobe, general styling advice for
        the item rather than an error or "".
    """
    items = (wardrobe or {}).get("items") or []

    system = (
        "You are a friendly secondhand-fashion stylist. Be specific and "
        "concise. Do not invent pieces the user does not own."
    )

    if not items:
        prompt = (
            "A shopper is considering this secondhand find. They have not "
            "saved any wardrobe, so give general styling advice.\n\n"
            f"Item: {_describe(new_item)}\n\n"
            "Suggest one or two outfit ideas built around this item, using "
            "common basics anyone is likely to own. Keep it under 120 words."
        )
    else:
        wardrobe_lines = "\n".join(f"- {_describe(piece)}" for piece in items)
        prompt = (
            "A shopper is considering this secondhand find:\n"
            f"{_describe(new_item)}\n\n"
            "Here is what they already own:\n"
            f"{wardrobe_lines}\n\n"
            "Suggest one or two outfits that combine the new item with "
            "specific pieces from their wardrobe. Name the wardrobe pieces "
            "you use. Keep it under 150 words."
        )

    text = generate(prompt, system=system).strip()
    if text:
        return text

    # The model answered with nothing. Never hand an empty string downstream.
    return (
        f"Style the {new_item.get('title', 'item')} with simple basics in a "
        "neutral colour and let it be the focus of the outfit."
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption. If `outfit` is empty or whitespace,
        a descriptive message string instead of an exception.
    """
    if not outfit or not outfit.strip():
        return "No outfit suggestion was available, so no fit card was written."

    title = new_item.get("title", "this find")
    price = _price_text(new_item.get("price"))
    platform = new_item.get("platform", "a resale app")

    system = (
        "You write short, casual social-media captions for thrift finds. "
        "Sound like a real person posting, not a product description."
    )
    prompt = (
        "Write a caption of 2 to 4 sentences about this thrift find.\n\n"
        f"Item: {title}\n"
        f"Price: {price}\n"
        f"Platform: {platform}\n"
        f"Outfit idea: {outfit}\n\n"
        "Rules:\n"
        f"- Mention the item, the exact price ({price}), and the platform "
        f"({platform}) once each.\n"
        "- Be specific about the vibe.\n"
        "- Do not use hashtags or a list. Plain sentences only."
    )

    text = generate(prompt, system=system).strip()
    if text:
        return text
    return f"Found the {title} for {price} on {platform}."