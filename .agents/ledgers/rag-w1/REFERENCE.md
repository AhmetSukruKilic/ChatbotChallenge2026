# RAG W1 — REFERENCE (read once, then no spelunking)

Verified 2026-10-21 at `071d622`. Reality diverges → trust code, fix this file.
All paths below relative to `submission_repo/` unless they start with `.agents/`.

## Layout

| Path | Status | What |
|---|---|---|
| `main.py` | **frozen** | grader entry. 1 question → `rag_answer`, >1 → `rag_answer_batch`. `TIME_LIMIT = 30`. Exception → `[""] * n` |
| `bot/llm.py` | given | `chat`, `embed(texts, batch_size=256)`, `describe_image`, private `_client(url)`, `CHAT_URL` `EMBED_URL` `VISION_URL`, `*_DEPLOYMENT`. Reads `.env` |
| `bot/store.py` | given | `get_store(path, name="chatbot", reset)`, `add_to_store(store, texts, metadatas, ids)`, `query(store, question, k, where)` → `[{text, metadata, distance}]`, squared L2, lower = closer. Read-only FS → copies index to temp. Monkeypatch `bot.store.embed` |
| `bot/answer.py` | ours (K05) | `CONFIG` (`k` 8, `k_image` 3, `budget_s` 25, `workers` 4), `SYSTEM_PROMPT`, `FEW_SHOT`, `_embed`/`_chat` (deadline-bounded via `_client().with_options`), `retrieve` (kept), `retrieve_vec`, `build_messages`, `clean_answer`, `_answer`, `rag_answer`, `rag_answer_batch`. `STORE_PATH` absolute |
| `build/scrape.py` | ours (K03) | `SITES`, `sitemap_urls`, `crawl` (fallback), `extract(html, url, page_type)`, `scrape()`. No gateway |
| `build/index.py` | ours (K04) | `CHUNK_SIZE, OVERLAP = 800, 100`, `SECTION_MAX = 1000`, `sections`, `chunk`, `text_chunks`, `image_chunks`, `build_index()` — full rebuild, `reset=True` |
| `build/images.py` | ours (K08 code) | `DESCRIPTION_PROMPT`, `priority`, `describe_all`, `_ask_vision`. CLI `--limit --workers --chat-model --no-index` |
| `build/evaluate.py` | ours (K02) | `score`, `hit`, `main()`. CLI `--set --note` |
| `check_setup.py` | given | live gateway check |
| `dev_set.json` | given | 15 `{level, question, answer}`, 3 per level 1–5. Workshop facts, not the live sites |
| `eval/` | generated | `experiment_log.csv` committed, `failures.json` gitignored |
| `data/` | generated | `pages.json`, `images.json`, `descriptions.json`, `chroma/` — all committed (ADR-K13) |

## Commands

Always from `submission_repo/`. Always `-m` for build modules: `python build/index.py` puts
`build/` on `sys.path[0]` and `from bot.store import ...` fails.

```bash
cd submission_repo
.venv/bin/python -m build.scrape                     # no gateway; agent may run (~5 min)

# GATEWAY — Ahmet runs these, VPN off (ADR-K11)
.venv/bin/python check_setup.py                      # want READY
.venv/bin/python -m build.index                      # full rebuild: pages + images + cached descriptions
.venv/bin/python -m build.images --limit 12 --no-index   # probe vision rate/quality
.venv/bin/python -m build.images --limit N           # describe top-priority N, then rebuild
.venv/bin/python -m build.evaluate --note "baseline"
.venv/bin/python main.py "What does FDM stand for in 3D printing?"
```

## Data contracts (between tasks)

`data/pages.json` — K03 → K04. Headings inline as `## ` lines in `text`:
```json
[{"url": "...", "site": "innowings.engg.hku.hk", "title": "...", "page_type": "post|page",
  "year": "2025|''", "text": "...\n## Heading\n..."}]
```

`data/images.json` — K03 → K04, K08:
```json
[{"src": "abs url", "alt": "", "caption": "", "page": "url", "page_title": "...", "year": ""}]
```

`data/descriptions.json` — K08 → K04: `{src: description}`.

Chunk metadata (str/int/bool only): text `url site title section position kind="text" page_type year`;
image `url image title section position kind="image" described page_type="image" year`.
Ids `t{i}`, `img{i}`.

`eval/experiment_log.csv` — appended by K02. Header:
`date,note,set,k,k_image,total,n,retrieved,per_level,mean_s,slowest_s`; `per_level` like `L1=3/3 L2=1.5/3`.

## Test conventions

Deferred (ADR-K16). Below is the plan for when the harness lands.


- `tests/conftest.py` (K01) provides fixtures:
  - `fake_embed` — deterministic: text → 16-dim vector from sha256 bytes. Same text, same vector.
  - `fake_chat` — records messages, returns a queued reply.
  - `tmp_repo` — `monkeypatch.chdir(tmp_path)`, so `data/chroma` lands in tmp.
- Monkeypatch where the name is looked up: `bot.store.embed`, `bot.answer.chat`,
  `build.scrape.requests.get`.
- `tests/fixtures/` holds HTML/sitemap fixtures. No real corpus text in fixtures.
- Test file per module: `tests/test_<module>.py`.

## Conventions

- Docs terse, search keys exact (`AGENTS.md`).
- Conventional Commits, scope = task ID: `feat(K05): labelled context and format guard`.
- No AI attribution in commits or PRs.
- Commit and push to `main` after each task; `data/chroma` committed by Ahmet (ADR-K13).
