# RAG W1 — PLAN (Architecture)

Written once. Amend only via a new `DECISIONS.md` ADR-K entry referenced here.
Codebase orientation: `REFERENCE.md` (read before any task).

## Goal

Own scraper + own index over both Inno Wing sites, a single-shot RAG answerer, and a committed
eval loop. By **23 Sep 2026**: bot scores above zero on Lv1 and Lv2 of `dev_set.json`, and every
tuning change is one row in `eval/experiment_log.csv`.

## The invariant this initiative must not weaken

> `python main.py "q"` prints one short answer per question, within 30s, never raises, on a
> read-only machine whose only network is the gateway.

Only known exception: gateway itself down — no answer possible, `rag_answer` returns `""` after
one retry. `main.py`, `bot/llm.py`, `bot/store.py`, `check_setup.py` stay untouched.

## Topology

```
BUILD (our laptops, unlimited time)                 RUNTIME (grader, 30s/question, read-only)
build/scrape.py ──► data/pages.json  (committed)     main.py (frozen)
               └──► data/images.json (committed)       └─► bot/answer.py rag_answer
build/index.py  ──► data/chroma      (seat A commits)        ├─ retrieve ─► bot/store.query ─► embed ─┐
               └──► data/index_meta.json                     └─ chat ───────────────────────────────┤
build/evaluate.py ─► eval/experiment_log.csv (committed)                                Azure gateway
                 └─► eval/failures.json (gitignored)          (only network allowed)  ◄──────────────┘
```

## Decision table (full ADRs in DECISIONS.md)

| # | Decision | Chosen | Reason |
|---|---|---|---|
| ADR-K01 | Scope | W1 only: Lv1+Lv2 above zero by 23 Sep | images, routing, Lv5 are W2 |
| ADR-K02 | Stack | gateway + Chroma only | zero new install risk; hybrid/OCR/rerank wait for W2 |
| ADR-K03 | Extraction | sitemap first; one content element; `img` records same pass | boilerplate crowds top-k; no second crawl |
| ADR-K04 | Chunking | heading-first, heading prepended, hash dedup, fallback 800/100 chars | fact stays with its section |
| ADR-K05 | Metadata | `url title section position kind page_type year` now | new field later = full rebuild |
| ADR-K06 | Runtime | single shot: top-k, labelled context, temp 0, few-shot, format guard | W1 enough; W2 adds routing |
| ADR-K07 | Failure | retrieval error → closed-book answer; batch isolates per question | `main.py:31-34` blanks whole batch on raise |
| ADR-K08 | Eval | `build/evaluate.py`: retrieval-hit and answer score split, per level, timing, CSV row, failures file | one change at a time, compared by numbers |
| ADR-K09 | Index sharing | `pages.json` committed; anyone builds `data/chroma` locally; only seat A commits it | binary files never merge |
| ADR-K10 | Tests | offline pytest, fake `embed`/`chat`; pytest in `requirements-dev.txt` | agents cannot reach gateway; grader install stays lean |
| ADR-K11 | Gateway runs | agent writes the command, human runs it | VPN → 403 (`.agents/docs/ENVIRONMENT.md`) |

## Retrieval + generation contract

- Chunk text = `"{title} — {section}\n{body}"`. Heading in the text, so the embedding sees it.
- `retrieve(question, k, where)` returns `store.query` dicts unchanged — eval reads them.
- Prompt: role, grounding, format, fallback (always guess), 3 invented few-shot pairs, context
  blocks `[i] title — url` + text. Few-shot never uses `dev_set.json` answers (leaks into eval).
- `clean_answer(question, reply)`: first non-empty line, strip `Answer:` prefix and trailing
  period; "how many" → first integer (number words one–twenty mapped). Empty after cleaning →
  raw reply.

## Scoring proxy (eval)

Judges are human; eval is a proxy. Normalize = lowercase, strip punctuation, drop articles.
- **retrieval hit**: every content token of expected answer appears in joined retrieved text.
- **answer**: 1 if normalized equal, or all expected tokens present and answer ≤ 3× expected
  length; 0.5 if ≥ half expected tokens present; else 0.

## Phasing / task clusters (see STATE.md ledger)

0. Harness (K01)
1. Parallel build: eval (K02), scrape (K03), index (K04), answer (K05)
2. Measure: baseline (K06), tuning (K07)

## Seats

| Seat | Person | Tasks |
|---|---|---|
| A — index owner | teammate | K03, K04, K06 |
| B — answer + eval | Ahmet | K01, K02, K05, K07 |

## Out of scope (post-W1)

Image descriptions (`build/images.py`), OCR, BM25/hybrid, reranking, query decomposition, level
routing, Lv4 counting via `where`, Lv5 photographs, Codabench packaging, per-call timeouts.
