# RAG W1 — State

Last updated: 2026-10-21
Last session ended: **K02–K05 done in one session (commit 071d622); K01 retired.** Deadline day
(prelim 21 Oct), team now solo (ADR-K12, ADR-K13). Agent scraped both sites itself: 1163 pages,
5247 images in `data/pages.json`/`images.json`. Code: `build/scrape.py`, `build/index.py` (6421
text chunks, image chunks from cache), `build/images.py` (priority-ordered, resumable),
`bot/answer.py` (top 8 + 3 image pool, 25s deadline, never raises), `build/evaluate.py`.
Verified only by scratch smoke script with fake gateway — nothing live yet. Next: Ahmet runs K06.

Prior: **Ledger written** 2026-09-16. No task started. Gateway green off-VPN (`READY`, chat 1.4s, embed 1.0s).

## Execution protocol (follow exactly)

Start from `EXECUTION_PROMPT.md`. Read this file → `REFERENCE.md` once → only your task file →
work, ticking checkboxes → run `## Verification` verbatim → fill `## Notes` → update ledger row,
"Current task", "Last session ended" → commit `type(ID): title` + push → **STOP.**

## Current task

**K06 — Baseline run** (Ahmet, gateway). Builds `data/chroma` live and gets the first number.
Then K08 (images) and K09 (submit). Trap: first `build.index` embeds 3.7M chars — ~1–3 min;
VPN on = 403.

## Environment

- `submission_repo/.venv`, Python 3.13.5, pinned `requirements.txt` installed, `.env` filled.
- `data/pages.json`, `data/images.json` committed. `data/chroma` not built yet.
- pytest not installed (ADR-K16).
- Gateway: VPN on → 403. Agents never run gateway commands (ADR-K11).

## Open blockers / decisions for the user

- **Codabench upload format + how grader gets the gateway key** — owner. Unblocks K09.

## Task ledger (K01–K09)

| ID | Title | Seat | Status | Depends on |
|----|-------|------|--------|------------|
| K01 | Offline test harness | B | retired | — |
| K02 | Eval script | B | done | — |
| K03 | Scraper | B | done | — |
| K04 | Indexer | B | done | — |
| K05 | Answerer | B | done | — |
| K06 | Baseline run | B | todo | K02, K03, K04, K05 |
| K07 | Tuning pass | B | todo | K06 |
| K08 | Image descriptions run | B | todo | K03, K04 |
| K09 | Prelim submission package | B | blocked | K06 |

## Critical path

K06 → K09 (deadline). K08 beside K06; its rebuild must land before K09 packages `data/chroma`.
K07 only with time left.

## Backlog (deferred — promote when trigger fires)

- **Write own dev questions (30–50)** — 15 is too few; one question = 7%. Trigger: K07 done.
- **Hybrid BM25 + RRF** — Trigger: failures show vocabulary mismatch on proper nouns.
- **Offline pytest harness** (old K01 scope) — Trigger: prelim submitted.
- **Lv4: decomposition + routing, `where` counting; page `year` from JSON-LD (976/1163 blank)** —
  final is ~30% Lv4. Trigger: prelim submitted.
- **Lv5: own photos through `build/images.py`** — final is ~40% Lv5. Trigger: prelim submitted.
- **OCR / two-pass descriptions for dense posters** (W2 slide 16–17). Trigger: K08 notes show
  `[unreadable]` on posters.
