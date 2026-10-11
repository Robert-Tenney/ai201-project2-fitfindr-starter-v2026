# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

A user types a plain-language request for a secondhand clothing item, such as
"vintage graphic tee under $30" or "90s track jacket in size M". FitFindr
searches a set of 40 listings, picks the best match, and asks a model to suggest
one or two outfits that combine it with pieces from the user's wardrobe. It then
returns a short, post-style fit card caption that names the item, its price, and
the platform it's listed on. If nothing matches, it stops early and says what to
change, such as raising the price limit, dropping the size, or using broader
keywords.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the listings in `data/listings.json` by an optional size and an optional price ceiling, scores what remains by keyword overlap with the description, and returns the best matches.
- **Inputs:** `description` (str), `size` (str or None), `max_price` (float or None). `None` skips that filter.
- **Returns:** A list of at most 10 (`config.SEARCH_RESULT_LIMIT`) listing dicts, best match first. Each dict has `id`, `title` (str), `description` (str), `category` (str), `style_tags` (list), `size` (str), `condition` (str), `price` (float), `colors` (list), `brand` (str or None), and `platform` (str).
- **When it has nothing:** Returns an empty list `[]`. Never `None`, never an exception.
- **Matching rules:** `max_price` is inclusive. A size matches when the requested size equals one whole token of the listing's size, compared case-insensitively. Tokens are split on `/` and spaces, so "M" matches "S/M" but not "us 9" or "XL". A listing with zero keyword overlap is dropped.
- **MCP:** This tool is registered in `mcp_server.py` with the same name, the same three inputs and types (`description: str`, `size: str | None`, `max_price: float | None`), and a description that states the empty case. The agent calls it through `mcp_client.call_tool`.

### `suggest_outfit`

- **What it does:** Calls the model to suggest one or two outfits built around the selected listing and the user's wardrobe.
- **Inputs:** `new_item` (dict, one listing from `search_listings`), `wardrobe` (dict with an `items` key holding a list of wardrobe item dicts).
- **Returns:** A single non-empty string of outfit suggestions. When the wardrobe has items, it names specific pieces the user already owns.
- **When it has nothing:** If `wardrobe["items"]` is empty, it returns a non-empty string of general styling advice for the item, with no wardrobe pieces mentioned. It does not raise and does not return `""`.

### `create_fit_card`

- **What it does:** Calls the model to write a short, post-style caption about the find.
- **Inputs:** `outfit` (str, the output of `suggest_outfit`), `new_item` (dict, the selected listing).
- **Returns:** A single string of 2 to 4 sentences that mentions the item, its price, and its platform once each.
- **When it has nothing:** If `outfit` is empty or whitespace, it returns a descriptive message string (for example, "No outfit suggestion was available, so no fit card was written.") without calling the model. It does not raise.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** After `search_listings` runs, if `session["search_results"]` is an empty list, the loop sets `session["error"]` to a message naming what to change (raise the price limit, drop the size, or use fewer or broader keywords), leaves `session["fit_card"]` as `None`, and returns the session without calling `suggest_outfit` or `create_fit_card`. Otherwise it stores the first result in `session["selected_item"]`, calls `suggest_outfit`, then calls `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex. A pattern pulls a price like "under $30" into `max_price` (float) and a size like "size M" or "in size M" into `size`. The remaining words become `description`. The result is stored in `session["parsed"]`.

**What moves through the session:** In order: `query` → `parsed` → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. Each tool reads its input back out of the session rather than receiving it directly from the previous call. `error` is `None` unless the run ended early.

**Other ways the loop stops early (unit 4):** The search step goes through MCP, so if the MCP server can't be reached, `run_agent` catches `MCPError` and sets `session["error"]`. If the model can't be reached, it catches `ModelUnavailable` in the `suggest_outfit` and `create_fit_card` steps and sets `session["error"]` the same way. In every early stop `session["fit_card"]` stays `None`. All of this is in `agent.py::run_agent`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask "red corduroy pants under $60"
[1] search_listings (via MCP)
      in:  description='red corduroy pants', size=None, max_price=60.0
      out: 4 items: Corduroy Wide-Leg Pants — Rust, Oversized Flannel Shirt — Plaid Red/Black, Low-Rise Cargo Pants — Khaki … +1 more
      →    first result id=lst_005
[2] branch
      →    results found, selected id=lst_005
[3] suggest_outfit
      in:  item id=lst_005, 10 wardrobe items
      out: Hey friend! Those rust corduroy pants are a gorgeous 70s find and will fit right into your earth-tone collecti…
[4] create_fit_card
      in:  item id=lst_005, outfit of 665 chars
      out: That buttery wide-leg corduroy in a rich rust shade has the absolute best vintage seventies energy. Snag them …

  Found:    Corduroy Wide-Leg Pants — Rust — $32.0 on depop

  Outfit:   Hey friend! Those rust corduroy pants are a gorgeous 70s find and will fit right into your earth-tone collection. 

**Outfit 1: Casual & Cozy**
Pair the rust cords with your **White ribbed tank top** tucked in to highlight the high waist. Layer your **Oversized grey crewneck sweatshirt** over top for a relaxed, textured look, and finish with your **Chunky white sneakers**. 

**Outfit 2: Vintage Edge**
Tuck the **White ribbed tank top** into the pants, add your **Brown leather belt** to tie the warm tones together, and throw on your **Vintage black denim jacket**. Ground the outfit with your **Black combat boots** for a cool contrast against the retro cords.

  Fit card: That buttery wide-leg corduroy in a rich rust shade has the absolute best vintage seventies energy. Snag them for $32 on depop before I change my mind and keep them forever. Style them casually with a tucked-in white tank, a cozy grey crewneck, and chunky sneakers for the ultimate autumn vibe.

1 model calls this session, 1 served from cache, 371 prompt + 66 output tokens
```

**The three tools, tested one at a time**

The tools were exercised through the full loop and the eval rather than as three
separate one-line terminal calls. The loop output above shows each tool's input
and output in order: `search_listings` returned 4 listings, `suggest_outfit`
returned text that names wardrobe pieces ("White ribbed tank top", "Brown leather
belt"), and `create_fit_card` returned a three-sentence caption with the price
($32) and platform (depop). The empty-wardrobe run in Failure Modes shows
`suggest_outfit` with no wardrobe items, and the empty-search run shows
`search_listings` returning `[]`. I did not save separate `python -c` terminal
tests for each tool.

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I gave Claude `agent.py`, `generate.py` and the Milestone 2 brief and asked for the failure handlers and trace calls.
- *What came back:* `generate.py` already raised `ModelUnavailable` with a readable message, but nothing in `run_agent` caught it, so the user would have seen a raw `ModelUnavailable: ...` exception line. Claude added handlers in the `suggest` and `card` steps that set `session["error"]`, plus a `trace.step()` call per step with the MCP search labelled `search_listings (via MCP)`.
- *What I changed:* I ran the empty search and the empty wardrobe myself and read the output as a user who can't see the code. The empty-search message already named three things to change, so I kept it. I used Claude's handler wording for the model-unavailable case as written.

**Moment 2**

- *What I asked for:* I asked Claude for a scorer to draft the PASS/FAIL cells from `results/run_2026-10-11_0954_before.md`.
- *What came back:* `score_results.py`. Its criterion 2 check rejected any results block containing the word `suggest_outfit`, but the branch step's trace note says "stopping before suggest_outfit", so every try would have failed.
- *What I changed:* I changed the check to look for the trace step line `[n] suggest_outfit` only, then re-ran the scorer on both results files. I also had it flag a criterion 5 query that returned no listings, which is how `dress under $25` was caught.

**Unit 4 note:** Claude wrote `score_results.py` to draft the PASS/FAIL cells, and
I checked its output against the console traces for criteria 1, 2, 3 and 5. I did
not change any of its verdicts. For Milestone 5 I asked Claude for a change to
the `create_fit_card` prompt. It proposed telling the model the poster bought the
item and banning "listed". I checked that against the fit cards in my before-run
and kept it as one change. The after-run showed it only partly worked (7 of 25
cards in the seller's voice before, 5 of 25 after), and I reported that rather
than calling it fixed.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

Run: `python run_eval.py --label before` on 2026-10-11 09:54, cache off, five tries
per scenario, 120 model calls. Results file: `results/run_2026-10-11_0954_before.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item the search found is the item the next tool received | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card is a usable caption and doesn't repeat itself | 5 of 5 rounds* | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. A price ceiling is always respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

\*Criterion 4 as written in `criteria.md` asks for at least 4 of 5 cards well
formed (2 to 4 sentences, exact price, platform name) and no two sharing a first
sentence. Criteria 4 and 5 each use five different scenarios, so Try k is round
k across all five (the k-th card of each of the five items, or the k-th run of
each of the five price-ceiling queries). A round passes when it meets the
criterion as written. I read the row against 5 of 5 rounds because the
no-shared-first-sentence part has no allowance.

**How I scored the tries:** Criteria 1, 2 and 3 are read directly from the trace
printed by `run_eval.py`: every try of the matching query printed all four steps
and a fit card; every try of the impossible query stopped after step 2; every
try of the state query showed the same id at all four points. Criteria 4 and 5
were scored with `score_results.py` and checked by hand against the raw results
file. The scorer's output matched my reading of the console traces for criteria
1, 2, 3 and 5, and I did not change any of its verdicts.

**A query that tested nothing:** one of the five criterion 5 queries, `dress under
$25`, matched no listings on any of the five tries (`search_listings (via MCP)`
returned `[] (empty)` and the loop stopped at the branch). An empty result cannot
exceed a price ceiling, so that query passes without testing the filter. The
scorer flagged it too ("returned no listings, so it tested nothing").
Criterion 5 was therefore tested by four real queries, not five. I kept the run
and the scenario unchanged so the before and after runs stay comparable.

**Real output from one try**, pasted as text, naming the file and function
that produced it:

Criterion 1 — `agent.py::run_agent`, run by `run_eval.py::main` (scenario "matching
query completes", try 1; the fit card text is truncated in the trace, so the full
card is in the results file):

```
[1] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey, Y2K Baby Tee — Butterfly Print … +7 more
      →    first result id=lst_006
[2] branch
      →    results found, selected id=lst_006
[3] suggest_outfit
      in:  item id=lst_006, 10 wardrobe items
      out: Hey! That bootleg graphic tee is an absolute score for a grunge-streetwear vibe. Since it has a slightly boxy …
[4] create_fit_card
      in:  item id=lst_006, outfit of 934 chars
      out: This faded black jersey cotton tee has the best boxy 2003 tour bootleg cut imaginable! Snagged it on depop for…
  try 1: completed — fit card 261 chars
```

Criterion 2 — `agent.py::run_agent` and `agent.py::_no_results_message` (scenario
"impossible query stops early", try 1). The console line is cut at 60 characters,
so the full message is in the results file and in Failure Modes below:

```
[1] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
[2] branch
      →    search_results is empty, stopping before suggest_outfit
  try 1: stopped early — No listings matched 'designer ballgown' in size XXS under $5
```

Criterion 3 — trace lines from `agent.py::run_agent` (scenario "state: ids match",
try 1; all five tries show `lst_004` at all four points):

```
      →    first result id=lst_004
      →    results found, selected id=lst_004
[3] suggest_outfit
      in:  item id=lst_004, 10 wardrobe items
[4] create_fit_card
      in:  item id=lst_004, outfit of 732 chars
```

Criterion 4 — `tools.py::create_fit_card`. The trace truncates cards, so these are
the full cards from the runs shown in this README (the complete round-by-round
cards are in `results/run_2026-10-11_0954_before.md`). Each has 3 sentences, the
exact price and the platform:

```
(red corduroy pants, depop, $32)
That buttery wide-leg corduroy in a rich rust shade has the absolute best vintage seventies energy. Snag them for $32 on depop before I change my mind and keep them forever. Style them casually with a tucked-in white tank, a cozy grey crewneck, and chunky sneakers for the ultimate autumn vibe.

(denim jacket, poshmark, $42)
That faded light wash denim has the absolute best vintage broken in feel you could ever ask for. I have it listed over on poshmark right now for just $42 so you can grab it. Throw this cropped cut over a classic black slip dress with chunky boots and you are completely ready to go!
```

Criterion 5 — `tools.py::search_listings`, called through `mcp_server.py`. The
selected item for each of the four queries that matched, each under its ceiling
(the filter in `search_listings` is a plain `price > max_price` comparison):

```
graphic tee under $30   -> Graphic Tee — 2003 Tour Bootleg Style, $24
jacket under $40        -> Shacket — Olive Canvas, $33
jeans under $35         -> Straight Leg Black Jeans — Faded, $30
sneakers under $45      -> Low-Top Canvas Sneakers — Off-White, $20
dress under $25         -> [] (no listings, tested nothing)
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | MET (5/5) | 5 PASS cells against a 4 of 5 target. All five tries printed all four trace steps and ended with a fit card. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | 5 PASS cells against a 5 of 5 target. Every try's trace ends at step 2, the branch, and shows no `suggest_outfit` step. |
| 3 | The item the search found is the item the next tool received | 5 of 5 | MET (5/5) | 5 PASS cells against a 5 of 5 target. In every try `lst_004` appears as the first result, the selected item, and the input to both later tools. |
| 4 | The fit card is a usable caption and doesn't repeat itself | 5 of 5 rounds | MET (5/5) | 5 PASS cells against a 5 of 5 target. In every round at least 4 of the 5 cards had 2 to 4 sentences, the exact price and the platform name, and no two of the five cards shared a first sentence. |
| 5 | A price ceiling is always respected | 5 of 5 | MET (5/5) | 5 PASS cells against a 5 of 5 target, but only four of the five queries returned listings, so the check was weaker than the table suggests. |

**Diagnoses**

All five criteria were met, so none needs a diagnosis. Criterion 1's target
allowed for rate-limit failures and keyword misses. Rate-limit pauses did occur
(`[rate limit] 15 requests used this minute. Waiting 36s`) in several tries,
and none of them ended a run, so that risk did not turn into a failure here.

**A defect the criteria did not measure.** Several fit cards read as if the poster
is selling the item, not showing off a purchase: "I just listed it on depop"
(graphic tee try 2), "It is listed on depop right now f…" (slip dress try 2),
"I have it listed on…" (graphic tee try 4). The scorer counted 7 of 25
criterion 4 cards containing "listed" or "listing" in the before run. Place: the
model's output. Mechanism: the `create_fit_card` prompt in `tools.py` gives the
platform and price but never says who the poster is, so the model sometimes picks
the seller's voice. The tool returned a valid string every time; the prompt left
the point of view open. This is what I chose to fix in Milestone 5.

**Other things I noticed, not fixed.** `suggest_outfit` sometimes prints internal
ids in text meant for the user: sneakers tries 1 and 5 show `lst_019`, denim
jacket try 4 shows `lst_007`, and jeans try 3 shows `w_001`. Place: the model's
output, caused by `_describe` in `tools.py`, which passes every field including
`id` into the prompt. Fit card openers also repeat across tries of the same item
(for example "That faded black cotton has the most unreal..." in graphic tee
tries 2, 3 and 4). Criterion 4 only compares first sentences across five
different items, so this does not count against it.

**Pattern:** I missed nothing, but criterion 4 passed 5/5 while a visible defect
remained: 7 of 25 fit cards in the before run were written in the seller's voice
("I just listed it on depop"). The criterion checks length, price, platform and
distinct openers, and a card in the wrong voice satisfies all four. So the
criterion is measurable but does not measure what I care about. The
deterministic parts (search, branch, session) did not fail.

**Which target was too easy:** criterion 5. It cannot fail for a query that
matches nothing, as `dress under $25` showed, and the filter is a plain numeric
comparison, so five tries add nothing beyond one. I would tighten it to require
at least one result per query.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

These two traces are from `run_eval.py` (try 1 of each scenario), which prints the
same `trace.step()` lines as `python app.py ask '...' --trace`. The empty-search
trace is two steps; the happy path is four.

**Happy path**

```
[1] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey, Y2K Baby Tee — Butterfly Print … +7 more
      →    first result id=lst_006
[2] branch
      →    results found, selected id=lst_006
[3] suggest_outfit
      in:  item id=lst_006, 10 wardrobe items
      out: Hey! That bootleg graphic tee is an absolute score for a grunge-streetwear vibe. Since it has a slightly boxy …
[4] create_fit_card
      in:  item id=lst_006, outfit of 934 chars
      out: This faded black jersey cotton tee has the best boxy 2003 tour bootleg cut imaginable! Snagged it on depop for…
```

**Empty search**

```
[1] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
[2] branch
      →    search_results is empty, stopping before suggest_outfit
```

**On the MCP move:** In `mcp_server.py` I registered `search_listings` with
`@mcp.tool()`, with typed inputs (`description: str`, `size: str | None`,
`max_price: float | None`) and a description that names units and the empty case.
In `agent.py::run_agent` I replaced the direct call `search_listings(...)` with
`mcp_client.call_tool("search_listings", {...})` and added an `MCPError` handler.
Across both eval runs (240 model calls in total), every search went through
`search_listings (via MCP)` with no `MCPError`, including the empty results, which
came back as `[] (empty)` and so still triggered the branch. The results also
looked the same as a direct call would: the listing counts and ids in the traces
(for example 10 items, first id `lst_006`, for "vintage graphic tee under $30")
are consistent from try to try, and an empty result came back as an empty list,
not a string, so the loop's branch kept working. I did not run a separate
side-by-side comparison of the direct call and the MCP call.

**Did anything behave differently after the move?** Nothing in the returned
results changed: lists of listing dicts came back as lists, and `[]` still
triggered the branch. The visible difference is cost: `mcp_client.call_tool`
starts `mcp_server.py` as a separate process for every call, so each search
carries that startup time, which a direct function call does not. Only
`search_listings` was moved; `suggest_outfit` and `create_fit_card` still run
directly.

### Failure Modes (Milestone 2)

I triggered each failure one at a time. The output below is what the agent
printed.

**1. Empty search**

```
$ python app.py ask "designer ballgown size XXS under $5" --trace
[1] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
[2] branch
      →    search_results is empty, stopping before suggest_outfit

  No listings matched 'designer ballgown' in size XXS under $5. You could raise your price limit above $5, drop or change the size (XXS), or use fewer or broader keywords (for example 'dress' instead of a long description).

0 model calls this session
```

The loop stopped at step 2, made no model calls, and the message names three
things the user can change.

**2. Empty wardrobe**

```
$ python app.py ask "denim jacket under $50" --empty-wardrobe --trace
(running with an empty wardrobe)
[1] search_listings (via MCP)
      in:  description='denim jacket', size=None, max_price=50.0
      out: 7 items: Denim Jacket — Light Wash, Cropped, 90s Track Jacket — Navy/White Stripe, High-Waisted Denim Shorts — Cutoff … +4 more
      →    first result id=lst_007
[2] branch
      →    results found, selected id=lst_007
[3] suggest_outfit
      in:  item id=lst_007, 0 wardrobe items
      out: This vintage Wrangler cropped denim jacket is such a versatile find! Here are two easy ways to style it using …
[4] create_fit_card
      in:  item id=lst_007, outfit of 541 chars
      out: That faded light wash denim has the absolute best vintage broken in feel you could ever ask for. I have it lis…

  Found:    Denim Jacket — Light Wash, Cropped — $42.0 on poshmark

  Outfit:   This vintage Wrangler cropped denim jacket is such a versatile find! Here are two easy ways to style it using items you likely already own:

**1. Casual Streetwear:** Throw it over a classic white t-shirt paired with black leggings or biker shorts. Finish the look with fresh white sneakers and a crossbody bag for an effortless, on-the-go vibe.

**2. Elevated Casual:** Layer the jacket over a simple black slip dress or a ribbed midi dress. Add chunky black boots to balance the cropped silhouette and give the outfit a cool, vintage edge.

  Fit card: That faded light wash denim has the absolute best vintage broken in feel you could ever ask for. I have it listed over on poshmark right now for just $42 so you can grab it. Throw this cropped cut over a classic black slip dress with chunky boots and you are completely ready to go!

1 model calls this session, 1 served from cache, 331 prompt + 61 output tokens
```

No crash and no empty string: with nothing in the wardrobe, `suggest_outfit`
returned general advice using common basics and named no wardrobe pieces. (This
run used the Milestone 5 prompt, and the fit card still says "I have it listed
over on poshmark", which is the seller's voice the change was meant to remove.)

**3. Model unavailable**

My first attempt did not trigger this failure. I ran
`python app.py ask "red corduroy pants under $60"` without disabling the cache,
and it succeeded; its last line read `1 model calls this session, 1 served from
cache` (output in Sample Run). The cache key is built from the prompt, which
contains the item and the wardrobe rather than the query text, so a new query that
finds an already-seen listing is answered from cache and never calls the model.

The handler is in `agent.py::run_agent` (the `suggest` and `card` steps catch
`ModelUnavailable`). Given the code, a bad key produces this message from
`generate.py::_explain` wrapped by the loop:

```
The styling model couldn't be reached, so no outfit was made. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Fix that, then run the same search again.
```

I am showing that as what the code is written to produce, not as output I
captured. To capture it, set `AI201_CACHE=0`, change one character of
`GEMINI_API_KEY`, run a query, and restore the key.

**What I changed:** `ModelUnavailable` was raised by `generate.py` but nothing in
`agent.py` caught it, so the user saw a raw exception line. I added handlers in
the `suggest` and `card` steps of `agent.py::run_agent`. Each one sets
`session["error"]` to a message naming what broke and what to do next. The empty
search and empty wardrobe already behaved correctly and needed no handler.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One prompt, in `tools.py::create_fit_card`. Nothing else in the
repo changed between the before run and the after run (`scenarios.py` and
`agent.py` are identical, and `score_results.py` only gained a diagnostic count
that I also ran on the before file).

Before, the prompt said:

```
Write a caption of 2 to 4 sentences about this thrift find.
...
- Mention the item, the exact price ({price}), and the platform ({platform}) once each.
- Be specific about the vibe.
- Do not use hashtags or a list. Plain sentences only.
```

After, it says who the poster is and bans the seller's voice:

```
Write a caption of 2 to 4 sentences about this thrift find. The person posting
BOUGHT it secondhand and is showing it off. They are not selling it.
...
- Mention the item, the exact price ({price}), and the platform ({platform}) once
  each, as the place they bought it and what it cost.
- Say they bought, scored or found it. Never say they listed it or are selling it.
- Be specific about the vibe.
- Do not use hashtags or a list. Plain sentences only.
```

**Which failure it was meant to fix:** The model's output, from the defect in
Verdicts and Diagnoses: fit cards written in the seller's voice ("I just listed it
on depop"), because the prompt never said the poster bought the item. It targets
no criterion directly, so I measured it with a diagnostic count of fit cards
containing "listed" or "listing", taken from the same scorer on both files.

### Run Log — After

Run: `python run_eval.py --label after` on 2026-10-11 10:23, cache off, five tries
per scenario, 120 model calls. Results file: `results/run_2026-10-11_1023_after.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item the search found is the item the next tool received | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card is a usable caption and doesn't repeat itself | 5 of 5 rounds | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. A price ceiling is always respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

`dress under $25` again returned `[]` on all five tries, so criterion 5 again
tested four queries.

Diagnostic, from `score_results.py` on each file:

| Run | Fit cards saying the poster "listed" the item (criterion 4 scenarios, 25 cards) |
|---|---|
| Before (`run_2026-10-11_0954_before.md`) | 7 of 25 |
| After (`run_2026-10-11_1023_after.md`) | 5 of 25 |

**Did it help, and how do I know:** Slightly, but not enough to call it fixed. The
count of fit cards in the seller's voice fell from 7 of 25 to 5 of 25 (28% to
20%). That is a drop of two cards from one run each at temperature 0.9, so it
could be noise: I would need several runs per version to tell. Criteria 1 to 5
were 5/5 in both runs, so the prompt change broke nothing, and it also moved no
criterion, because none of them measures this defect. The seller's voice still
appears after the change, for example "I just listed t…" in track jacket try 3,
and in the empty-wardrobe scenario, which is outside the 25 ("It is listed for
$42 on poshmark right now…"). A later single run with the new prompt, the
empty-wardrobe command in Failure Modes above, again produced "I have it listed
over on poshmark right now for just $42", so the change did not remove the
problem. A likely reason it only partly worked: the prompt says what not to say,
but the outfit text passed in reads like advice to a buyer, and at temperature
0.9 the model still sometimes slips into the seller's voice. The scorer matches
any card containing "listed" or "listing", so a harmless use of the word would
also count, which means 5 of 25 is an upper bound on real seller's-voice cards.

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No criterion is still missed: all five were MET in the after run. What remains is
what the criteria do not measure.

**Seller's voice in fit cards (not a criterion).** 5 of 25 criterion 4 cards after
the change, down from 7 of 25, and it reappeared in a later single run. What I
would do next: add the same rule to the `system` string in `create_fit_card`, and
if that is not enough, make the function check for "listed" or "selling" and
regenerate once, in `tools.py::create_fit_card`. I would also add a criterion
that measures it, since criterion 4 cannot see it. I stopped because each of
those is a second change and I wanted one measured change.

**Internal ids in `suggest_outfit` text.** Still present after the change, because
I did not touch it: `lst_019` in sneakers tries 1 and 4, `w_001` in jeans tries 1,
2 and 3, `w_007` in the sneakers price try 2. The fix is to drop `id` from what
`_describe` passes to the model, in `tools.py`. I stopped for the same reason.

**The response cache can hide a model failure.** The cache key is built from the
prompt (item and wardrobe), not the query, so a different query that finds the
same listing is answered from cache without calling the model. My first attempt
at the model-unavailable test passed for that reason. The fix for testing is
`AI201_CACHE=0`; I did not change the code. I also never captured the real
model-unavailable message, so that handler is untested by me.

**Known limits I did not test:** the `dress under $25` query matched nothing in
either run, so criterion 5 tested four queries, not five. Every `call_tool`
starts a new server process, which is slow. `search_listings` is keyword
matching, so a synonym will miss a listing that exists. Only `search_listings`
went through MCP.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**