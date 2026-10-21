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

## ADR-K12 — 2026-10-21 — Prelim scope: Lv1–Lv3, one session (supersedes ADR-K01)

**Context:** Nothing built by 21 Oct, the preliminary deadline (W0 slide 2: code and vector
database through Codabench). Prelim weights (W0 slide 4): Lv1 30, Lv2 30, **Lv3 40**, Lv4 0,
Lv5 0. W1-only scope leaves 40% on the table.
**Decision:** Scope = Lv1 + Lv2 + Lv3 for the prelim. Image pipeline (`build/images.py`) in.
Lv4 decomposition/routing and Lv5 photos stay out until the final (28 Oct).
**Consequences:** ADR-K01 no longer governs; K01–K07 Notes quoting it were true when written.

## ADR-K13 — 2026-10-21 — Solo team, Ahmet owns the index (supersedes ADR-K09)

**Context:** Owner, 2026-10-21: "we are alone no need for teammates". Seat A does not exist, so
the two-writers binary conflict ADR-K09 guards against cannot happen.
**Decision:** One seat. Ahmet runs and commits `data/chroma`. `data/pages.json`,
`data/images.json`, `data/descriptions.json` committed too.
**Consequences:** ADR-K09 no longer governs. Every task is Ahmet's.

## ADR-K14 — 2026-10-21 — Two retrieval pools, deadline-bounded calls (supersedes ADR-K06)

**Context:** Lv3 answers live in image descriptions, which compete with 6421 text chunks for
the top k; a text-heavy top 8 can hide every image. `bot.llm.chat`/`embed` take no timeout and
the openai client defaults to 600s + 2 retries, so one stall breaks the 30s limit.
**Decision:** Per question: one embed; top `k=8` of any kind + top `k_image=3` with
`where={"kind": "image"}`, merged by distance, deduped. One `gpt-4o-mini` call, temp 0, 3
invented few-shot pairs, `IMAGE`/`PAGE` labelled context, `clean_answer` format guard. Calls go
through `bot.llm._client(...).with_options(timeout, max_retries)` against a 25s per-question
deadline; chat retried once if time remains. Batch: one embed for all questions, 4 threads.
**Why not edit `llm.py`:** frozen file (AGENTS.md).
**Consequences:** ADR-K06 no longer governs. ADR-K07 (degrade, never raise) still holds.
`answer.py` depends on `bot.llm` private `_client` and `*_URL` names.

## ADR-K15 — 2026-10-21 — Image descriptions cached, priority-ordered, folded into one index

**Context:** Scrape found 5247 images; gpt-5-mini at a few seconds each is hours, more than
the deadline allows.
**Decision:** `build/images.py` describes with the vision deployment (`--chat-model` for
gpt-4o-mini), 6 threads, extraction prompt (type, subject, verbatim text, counts, layout,
colours) with page title/alt/caption as context. Cache `data/descriptions.json` keyed by
`src`, saved every 20, resumable. Order by `priority()`: poster/award/map/venue-like names,
2025+ uploads, PNG, captioned first, so `--limit N` spends budget there. `build/index.py`
rebuilds the whole store from pages + images + cache; undescribed images with alt ≥ 15 chars
or a caption are indexed from that text alone.
**Consequences:** Rerunning `build.images` re-embeds everything (minutes, not hours).
Coverage grows with each run; nothing is lost on interrupt.

## ADR-K16 — 2026-10-21 — Offline pytest deferred to after prelim (supersedes ADR-K10)

**Context:** Deadline day. Harness (K01) would have gated every task.
**Decision:** Verify with a scratch smoke script (fake embed/chat, temp store) per session;
pytest harness moves to backlog.
**Consequences:** ADR-K10 no longer governs. K01 retired. No committed regression tests yet.
