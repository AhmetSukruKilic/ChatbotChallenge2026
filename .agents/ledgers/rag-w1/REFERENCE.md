# RAG W1 — REFERENCE (read once, then no spelunking)

Verified 2026-09-16 at `46ee954`. Reality diverges → trust code, fix this file.
All paths below relative to `submission_repo/` unless they start with `.agents/`.

## Layout

| Path | Status | What |
|---|---|---|
| `main.py` | **frozen** | grader entry. 1 question → `rag_answer`, >1 → `rag_answer_batch`. `TIME_LIMIT = 30` :16. Exception → `[""] * n` :31-34 |
| `bot/llm.py` | given | `chat(messages, model, temperature=0.0, max_tokens=512)` :63, `embed(texts, batch_size=256)` :79. Reads `.env` |
| `bot/store.py` | given | `get_store(path="data/chroma", name="chatbot", reset)` :41, `add_to_store(store, texts, metadatas, ids)` :82, `query(store, question, k, where)` :94 → `[{text, metadata, distance}]`, squared L2, lower = closer. `store.py` does `from bot.llm import embed` — monkeypatch `bot.store.embed`, not `bot.llm.embed` |
| `bot/answer.py` | ours (K05) | `SYSTEM_PROMPT` :13, `CONFIG` :24, `retrieve` :29 (keep it), `rag_answer` :41, `rag_answer_batch` :67 |
| `build/scrape.py` | ours (K03) | `SITES` :17 empty, `crawl` :22, `extract` :48 |
| `build/index.py` | ours (K04) | `CHUNK_SIZE, OVERLAP = 800, 100` :14, `chunk` :17, `build_index` :33 |
| `build/images.py` | W2, untouched | |
| `build/evaluate.py` | ours (K02), new | |
| `check_setup.py` | given | live gateway check |
| `dev_set.json` | given | 15 `{level, question, answer}`, 3 per level 1–5 |
| `tests/` | new (K01) | offline pytest |
| `eval/` | new (K02) | `experiment_log.csv` committed, `failures.json` gitignored |
| `data/` | generated | `pages.json`, `images.json`, `index_meta.json`, `chroma/` |

## Commands

Always from `submission_repo/`. Always `-m` for build modules: `python build/index.py` puts
`build/` on `sys.path[0]` and `from bot.store import ...` fails.

```bash
cd submission_repo
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt   # PyPI only, no gateway
.venv/bin/python -m pytest -q                                          # offline, agent may run

# GATEWAY — human runs these, VPN off (ADR-K11)
.venv/bin/python check_setup.py                                        # want READY
.venv/bin/python -m build.scrape                                       # no gateway, but hits the sites
.venv/bin/python -m build.index                                        # embeds everything
.venv/bin/python -m build.evaluate --change "baseline" --who ahmet
.venv/bin/python main.py "What is the capacity of Makerspace A?"
```

`build.scrape` needs only the public sites, not the gateway — an agent may run it if the sites
are reachable from its network.

## Data contracts (between tasks)

`data/pages.json` — written by K03, read by K04:
```json
[{"url": "...", "title": "...", "text": "full content text",
  "sections": [{"heading": "...", "text": "..."}],
  "images": [{"src": "abs url", "alt": "", "caption": "", "page": "url"}]}]
```

Chunk metadata — written by K04, read by K02/K05 (ADR-K05). All values str or int:
`url, title, section, position, kind="text", page_type, year`.

`data/index_meta.json` — written by K04, read by K02:
```json
{"chunk_size": 800, "overlap": 100, "n_chunks": 0, "n_pages": 0, "built_at": "ISO-8601"}
```

`eval/experiment_log.csv` — appended by K02. Header, fixed order:
`timestamp,who,change,chunk_size,overlap,k,retrieved,score,L1,L2,L3,L4,L5,mean_s,slowest_s,over_30s`
`retrieved` = hits out of 15, `score` = sum of 0/0.5/1 out of 15, `L1..L5` = score per level out of 3.

## Test conventions

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
- Commit and push to `main` after each task; `data/chroma` staged by seat A only (ADR-K09).
