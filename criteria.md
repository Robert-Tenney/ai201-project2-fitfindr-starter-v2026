# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all
three tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:** Not 5 of 5, because this path depends on things I don't
control. My search is a plain keyword match, so some phrasings of a query will
miss a listing that exists. Two of the three tools also call the model, so a
rate-limit pause or a failed call can end a run even when my code is right.
Not lower than 4, because for a query I've checked against the data, the search
should find something nearly every time.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:** This path never touches the model. It is a Python filter
followed by one `if` on an empty list, and the same input gives the same result
every time. If it fails even once, that is a bug in my branch, not bad luck, so
nothing short of 5 of 5 is acceptable.

---

## 3. The item the search found is the item the next tool received

In 5 of 5 happy-path runs, the `id` of `session["selected_item"]` equals the
`id` of `session["search_results"][0]`, and the item passed into
`suggest_outfit` and into `create_fit_card` has that same `id`. I check it by
printing the three ids at the end of the run. Any mismatch is a failure.

**Why this target:** Passing a dict from one step to the next is plain Python
with no randomness, and I'm routing every value through the session. There is
no reason for it to fail occasionally, so a single mismatch means the loop is
reading from the wrong place. A state failure looks like a bad outfit
suggestion, which is why I'm checking the ids directly and not the model's
words.

---

## 4. The fit card is a usable caption and doesn't repeat itself

For 5 different items, in at least 4 of 5 the fit card is 2 to 4 sentences
long and contains that item's exact price and its platform name. Across the
same 5 cards, no two share the same first sentence.

**Why this target:** The card comes from a model at temperature 0.9, so the
wording will differ and I can't check exact text. I can check things a person
would notice: it's caption-length, and it names the price and platform that
the tool is told to include. I picked 4 of 5, not 5 of 5, because a model
sometimes drops a detail or runs a sentence long. I picked "no shared first
sentence" with no allowance because at this temperature two different items
sharing an opening line would mean the prompt is acting like a template.

---

## 5. A price ceiling is always respected

For 5 queries that each include a price ceiling (for example "under $30"),
every listing in `session["search_results"]` has a `price` less than or equal
to that ceiling, with zero exceptions, in 5 of 5 queries.

**Why this target:** Price filtering is a plain numeric comparison with no
model involved, so a single listing over the ceiling means a bug in my filter
or in how I parse the query. I care about it because the query parser is the
fragile part: in PowerShell a query in double quotes loses the `$30`, and the
search quietly runs with no ceiling at all. A deterministic rule gets the
strictest target.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->