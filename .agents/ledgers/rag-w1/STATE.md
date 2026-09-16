# RAG W1 — State

Last updated: 2026-09-16
Last session ended: **Ledger written.** No task started. Design agreed in chat 2026-09-16, all
of it recorded in `PLAN.md` + `DECISIONS.md`. Gateway confirmed green off-VPN (`READY`, chat
1.4s, embed 1.0s). K03 blocked on the two site URLs.

## Execution protocol (follow exactly)

Start from `EXECUTION_PROMPT.md`. Read this file → `REFERENCE.md` once → only your task file →
work, ticking checkboxes → run `## Verification` verbatim → fill `## Notes` → update ledger row,
"Current task", "Last session ended" → commit `type(ID): title` + push → **STOP.**

## Current task

**K01 — Offline test harness** (seat B, Ahmet). Everything else depends on it: no task can prove
itself without fake `embed`/`chat`. Trap: `bot/store.py` binds `embed` at import — patch
`bot.store.embed`.

## Environment

- `submission_repo/.venv` exists, Python 3.13.5, `requirements.txt` installed, `.env` filled.
- pytest **not** installed — K01 adds it.
- `data/` does not exist yet.
- Gateway: VPN on → 403. Agents never run gateway commands (ADR-K11).

## Open blockers / decisions for the user

- **Two Inno Wing site URLs** — owner pastes them. Unblocks K03 → K06 → K07.
- **Teammate's name** — seat A column says "teammate" until given. Blocks nothing.

## Task ledger (K01–K07)

| ID | Title | Seat | Status | Depends on |
|----|-------|------|--------|------------|
| K01 | Offline test harness | B | todo | — |
| K02 | Eval script | B | todo | K01 |
| K03 | Scraper | A | blocked | K01 |
| K04 | Indexer | A | todo | K01 |
| K05 | Answerer | B | todo | K01 |
| K06 | Baseline run | A | todo | K02, K03, K04, K05 |
| K07 | Tuning pass | B | todo | K06 |

## Critical path

K01 → K03 (URLs) → K06. K02, K04, K05 run beside it.

## Backlog (deferred — promote when trigger fires)

- **Per-call timeout on `chat`/`embed`** — openai client defaults to 600s + 2 retries; one stall
  eats the 30s budget. Trigger: any eval row with `slowest_s > 10`.
- **Batch embedding in `rag_answer_batch`** — one `embed` call for all questions. Trigger:
  `mean_s > 5`.
- **Write own dev questions (30–50)** — 15 is too few; one question = 7%. Trigger: K07 done.
- **Image descriptions (`build/images.py`)** — Lv3 = 40% of prelim. Trigger: Workshop 2, 30 Sep.
- **Hybrid BM25 + RRF** — Trigger: failures show vocabulary mismatch on proper nouns.
