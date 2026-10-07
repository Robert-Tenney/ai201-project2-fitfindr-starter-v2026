#!/usr/bin/env python3
"""
Draft scorer for the run log. Reads a results/run_*.md file written by
run_eval.py and applies the rules in criteria.md.

    python score_results.py results/run_2026-10-07_1530_before.md

It makes NO model calls. Criterion 5 is checked by re-running the search
directly (no model involved), the rest are read out of the saved results.
Check its verdicts against the raw output before you paste them.
"""

import re
import sys

import scenarios as scenario_module
from agent import _parse_query
from tools import _price_text, search_listings

# Decide these BEFORE you look at results. Criterion 4's "at least 4 of 5"
# allowance is already inside each try (4 of 5 cards well formed), so the row
# target across the five tries is 5 of 5 here. Change it if your table says
# otherwise.
TARGETS = {1: 4, 2: 5, 3: 5, 4: 5, 5: 5}


def parse(path):
    text = open(path, encoding="utf-8").read()
    text = text.split("## What actually happened", 1)[1]
    data = {}
    for section in re.split(r"\n### ", "\n" + text)[1:]:
        name = section.split("\n", 1)[0].strip()
        tries = {}
        for block in re.split(r"\*\*Try (\d+)\*\*", section)[1:]:
            pass
        parts = re.split(r"\*\*Try (\d+)\*\*", section)
        for i in range(1, len(parts), 2):
            tries[int(parts[i])] = parts[i + 1]
        data[name] = tries
    return data


def completed(block):
    return "Crashed:" not in block and "- stopped early: no" in block and "Fit card:" in block


def fit_card(block):
    m = re.search(r"Fit card:\n\n```\n(.*?)\n```", block, re.S)
    return m.group(1).strip() if m else ""


def item_info(block):
    m = re.search(r"- selected_item: .* \(\$([\d.]+), ([^)]*)\)\n", block)
    return (float(m.group(1)), m.group(2).strip()) if m else (None, None)


def sentences(card):
    return [s for s in re.split(r"(?<=[.!?])\s+", card.strip()) if s]


def ids(block):
    first = re.search(r"first result id=(\S+)", block)
    chosen = re.search(r"selected id=(\S+)", block)
    sug = re.search(r"suggest_outfit\n\s+in:\s+item id=(\S+?),", block)
    card = re.search(r"create_fit_card\n\s+in:\s+item id=(\S+?),", block)
    return [m.group(1) if m else None for m in (first, chosen, sug, card)]


def main(path):
    data = parse(path)
    by_c = {}
    for s in scenario_module.SCENARIOS:
        if s.get("criterion"):
            by_c.setdefault(s["criterion"], []).append(s)

    rows = {c: {} for c in range(1, 6)}
    notes = []

    for t in range(1, 6):
        # 1: matching query completes
        s = by_c[1][0]
        rows[1][t] = completed(data[s["name"]][t])

        # 2: impossible query stops before tool 2
        # Milestone 4 fix: look for the trace STEP line "[n] suggest_outfit",
        # not the bare word, because the branch note says "stopping before
        # suggest_outfit" and used to make every try fail.
        b = data[by_c[2][0]["name"]][t]
        rows[2][t] = ("- stopped early: yes" in b) and "Fit card:" not in b \
            and not re.search(r"\[\d+\] suggest_outfit", b)

        # 3: four ids agree
        b = data[by_c[3][0]["name"]][t]
        got = ids(b)
        rows[3][t] = None not in got and len(set(got)) == 1
        if not rows[3][t]:
            notes.append(f"criterion 3 try {t}: ids {got}")

        # 4: round t across the five items
        cards = []
        good = 0
        for s in by_c[4]:
            b = data[s["name"]][t]
            card = fit_card(b)
            price, platform = item_info(b)
            ok = bool(card) and price is not None \
                and 2 <= len(sentences(card)) <= 4 \
                and _price_text(price) in card and platform.lower() in card.lower()
            good += ok
            if not ok:
                notes.append(f"criterion 4 try {t}: '{s['name']}' malformed "
                             f"({len(sentences(card))} sentences)")
            cards.append(sentences(card)[0] if sentences(card) else "")
        distinct = len(set(cards)) == len(cards)
        if not distinct:
            notes.append(f"criterion 4 try {t}: two cards share a first sentence")
        rows[4][t] = good >= 4 and distinct

        # 5: every result under each ceiling (direct call, no model)
        ok5 = True
        for s in by_c[5]:
            p = _parse_query(s["query"])
            for r in search_listings(p["description"], p["size"], p["max_price"]):
                if p["max_price"] is not None and r["price"] > p["max_price"]:
                    ok5 = False
                    notes.append(f"criterion 5: '{s['query']}' returned "
                                 f"{r['title']} at ${r['price']}")
        rows[5][t] = ok5

    print("| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |")
    print("|---|---|---|---|---|---|---|---|")
    for c in range(1, 6):
        marks = ["PASS" if rows[c][t] else "FAIL" for t in range(1, 6)]
        n = marks.count("PASS")
        verdict = f"{'MET' if n >= TARGETS[c] else 'MISSED'} ({n}/5)"
        print(f"| {c}. | {TARGETS[c]} of 5 | " + " | ".join(marks) + f" | {verdict} |")
    if notes:
        print("\nWhy things failed:")
        for n in notes:
            print("  -", n)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python score_results.py results/run_....md")
    main(sys.argv[1])