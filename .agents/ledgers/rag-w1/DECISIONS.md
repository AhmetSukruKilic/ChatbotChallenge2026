# RAG W1 — Decisions (append-only ADR log)

Never edit past entries. Supersede with a new dated entry. Prefix `ADR-K` — unique in this repo.

## ADR-K01 — 2026-09-16 — W1 scope only

**Context:** (A) all five levels (B) prelim first (C) prelim only. Owner: "we are rn doing only workshop 1".
**Decision:** Scrape, index, single-shot answer, eval. Target: Lv1+Lv2 > 0 on dev set by 23 Sep.
**Consequences:** Lv3 = 0 until W2 (40% of prelim). Metadata still stored for later (ADR-K05).

## ADR-K02 — 2026-09-16 — Given stack only

**Context:** (A) gateway+Chroma (B) +BM25 +build-time OCR (C) +local cross-encoder.
**Decision:** gateway (`gpt-4o-mini`, `text-embedding-3-small`) + `chromadb==1.5.9`. No new runtime deps.
**Why not C:** weights must ship in submission and load inside 30s on unseen machine.
**Consequences:** vocabulary mismatch on proper nouns unhandled until W2 hybrid.

## ADR-K03 — 2026-09-16 — Sitemap-first extraction, content element only

**Decision:** `scrape.py` reads `/sitemap.xml` per site, BFS crawl only if absent. Text from one
content selector per site, never whole `soup`. `img` records (`src` via `urljoin`, `alt`,
`caption`, `page`) collected in the same pass.
**Why not whole-page text:** nav/footer chunks score ~0.67 against unrelated queries (W1 slide 16).
**Consequences:** selector is per-site config; a redesigned site needs a new selector.

## ADR-K04 — 2026-09-16 — Heading-first chunking

**Decision:** pages carry `sections: [{heading, text}]`. Each section chunked alone at 800/100
chars; chunk text prefixed `"{title} — {heading}\n"`. Exact duplicate bodies dropped by sha1.
**Consequences:** `pages.json` schema gains `sections`; `text` kept for fallback.

## ADR-K05 — 2026-09-16 — Metadata stored now

**Decision:** every chunk: `url title section position kind page_type year`. `page_type` = first
URL path segment (`""` for root); `year` = first `20\d\d` in URL, else in title, else `""`.
Chroma metadata values are str/int only — never `None`.
**Consequences:** Lv4 `where` filters available in W2 without rebuild.

## ADR-K06 — 2026-09-16 — Single-shot runtime

**Decision:** retrieve k → labelled context → one `chat` at temperature 0 → `clean_answer`.
Few-shot pairs invented, never from `dev_set.json`.
**Consequences:** compound questions under-served until W2 decomposition.

## ADR-K07 — 2026-09-16 — Degrade, never raise

**Context:** `main.py:31-34` turns any exception into `""` for every question in the batch.
**Decision:** `rag_answer` catches retrieval errors → closed-book prompt. `chat` failure → one
retry → `""`. `rag_answer_batch` catches per question.
**Consequences:** index broken costs Lv2, not the run.

## ADR-K08 — 2026-09-16 — Committed eval script

**Decision:** `python -m build.evaluate --change "<text>" --who <name>` runs `dev_set.json`,
scores retrieval-hit and answer separately (PLAN § Scoring proxy), per level, per-question
seconds; appends one row to `eval/experiment_log.csv`; writes `eval/failures.json`.
**Why not notebook:** two people cannot compare hand-kept logs.
**Consequences:** auto-score is a proxy; read failures before trusting a delta.

## ADR-K09 — 2026-09-16 — Index sharing

**Context:** `submission_repo/.gitignore` warns not to ignore `data/chroma` — grader only has what
is committed. Two people committing it = unmergeable binary conflict.
**Decision:** `data/pages.json`, `data/images.json` committed. Anyone builds `data/chroma` locally.
Only seat A (teammate) stages `data/chroma`; seat B never does.
**Consequences:** seat B runs `python -m build.index` after pulling a new `pages.json`.

## ADR-K10 — 2026-09-16 — Offline tests

**Decision:** pytest in `submission_repo/requirements-dev.txt`; tests in `submission_repo/tests/`
monkeypatch `embed`/`chat`/`requests.get`. No test touches the gateway.
**Consequences:** agents can verify their own work; gateway behaviour verified by K06 only.

## ADR-K11 — 2026-09-16 — Humans run gateway commands

**Decision:** anything importing a live `bot.llm` call (`check_setup.py`, `main.py`,
`build.index`, `build.evaluate`) is written out for a human to run; agent waits for pasted output.
**Consequences:** K06/K07 are pair tasks: agent prepares, human runs, agent records.
