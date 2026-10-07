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
-  **MCP:** This tool is registered in `mcp_server.py` with the same name, the same three inputs and types (`description: str`, `size: str | None`, `max_price: float | None`), and a description that states the empty case. The agent calls it through `mcp_client.call_tool`.

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
$ python app.py ask '...'

PASTE YOUR REAL COMMAND AND OUTPUT HERE
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

PASTE YOUR REAL OUTPUT HERE
```

```
$ python -c "from tools import suggest_outfit; ..."

PASTE YOUR REAL COMMAND AND OUTPUT HERE
```

```
$ python -c "from tools import create_fit_card; ..."

PASTE YOUR REAL COMMAND AND OUTPUT HERE
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ADDED — unit 4 note: if you used score_results.py (written by Claude) to
     draft the PASS/FAIL cells, say so here, and say what you checked by hand
     and whether you changed any of its verdicts. -->

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

<!-- ADDED — the criterion names and targets come from criteria.md. Replace the
     blank Try and Verdict cells with PASS / FAIL and e.g. MET (5/5) from your
     own reading of results/run_<timestamp>_before.md. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 |  |  |  |  |  |  |
| 2. An impossible query stops before the second tool | 5 of 5 |  |  |  |  |  |  |
| 3. The item the search found is the item the next tool received | 5 of 5 |  |  |  |  |  |  |
| 4. The fit card is a usable caption and doesn't repeat itself | 5 of 5 rounds* |  |  |  |  |  |  |
| 5. A price ceiling is always respected | 5 of 5 |  |  |  |  |  |  |


\*Criterion 4 as written in `criteria.md` asks for at least 4 of 5 cards well
formed (2 to 4 sentences, exact price, platform name) and no two sharing a first
sentence. Criteria 4 and 5 each use five different scenarios, so Try k is round
k across all five (the k-th card of each of the five items, or the k-th run of
each of the five price-ceiling queries). A round passes when it meets the
criterion as written. I read the row against 5 of 5 rounds because the
no-shared-first-sentence part has no allowance. `EDIT THIS NOTE IF YOUR OWN
READING OF THE TARGET IS DIFFERENT.`


**How I scored the tries:** I ran `python run_eval.py --label before` (cache off,
five tries per scenario), then drafted the PASS/FAIL cells with
`score_results.py` and checked each one by hand against the raw results file.
`PASTE HOW MANY VERDICTS YOU CHANGED BY HAND, IF ANY, AND WHY.`

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```
PASTE REAL OUTPUT HERE
```

<!-- ADDED — one block per criterion, from a single try, as text. -->

**Criterion 1** — `agent.py::run_agent`, run by `run_eval.py::main`:

```
PASTE THE MATCHING-QUERY TRACE AND FIT CARD
```

**Criterion 2** — `agent.py::run_agent` and `agent.py::_no_results_message`:

```
PASTE THE IMPOSSIBLE-QUERY MESSAGE AND ITS SHORT TRACE
```

**Criterion 3** — trace lines from `agent.py::run_agent`:

```
PASTE THE FIRST-RESULT ID, SELECTED ID, suggest_outfit ID AND create_fit_card ID LINES
```

**Criterion 4** — `tools.py::create_fit_card`:

```
PASTE THE FIVE FIT CARDS FROM ONE ROUND
```

**Criterion 5** — `tools.py::search_listings`, called through `mcp_server.py`:

```
PASTE ONE QUERY AND THE PRICES RETURNED
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
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace

PASTE YOUR REAL TRACE HERE. It should show, in order:
[1] search_listings (via MCP)   (with "first result id=..." on its note line)
[2] branch
[3] suggest_outfit
[4] create_fit_card
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace

PASTE YOUR REAL TRACE HERE. It should stop after:
[1] search_listings (via MCP)
[2] branch
```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->

<!-- ADDED — edit the last sentence to match what you actually saw. -->
In `mcp_server.py` I registered `search_listings` with `@mcp.tool()`, with typed
inputs (`description: str`, `size: str | None`, `max_price: float | None`) and a
description that names units and the empty case. In `agent.py::run_agent` I
replaced the direct call `search_listings(...)` with
`mcp_client.call_tool("search_listings", {...})` and added an `MCPError`
handler. I compared the ids returned by the direct call and by the MCP call for
the same query: `PASTE THE TWO ID LISTS HERE, AND SAY WHETHER THEY MATCHED`.


### Failure Modes (Milestone 2)

I triggered each failure one at a time. The messages below are what the agent
printed.

**1. Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5'

PASTE THE EXACT MESSAGE HERE
```

**2. Empty wardrobe**

```
$ python app.py ask 'denim jacket under $50' --empty-wardrobe

PASTE THE EXACT OUTPUT HERE
```

**3. Model unavailable** (one character of the key changed in `.env`, then a query I hadn't asked before; the key has since been restored)

```
$ python app.py ask 'red corduroy pants under $60'

PASTE THE EXACT MESSAGE HERE
```

**What I changed:** `ModelUnavailable` was raised by `generate.py` but nothing in
`agent.py` caught it, so the user saw a raw exception line. I added handlers in
the `suggest` and `card` steps of `agent.py::run_agent`. Each one sets
`session["error"]` to a message naming what broke and what to do next.
`EDIT THIS LINE IF ANY OF THE THREE FAILURES BEHAVED DIFFERENTLY FOR YOU.`

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



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