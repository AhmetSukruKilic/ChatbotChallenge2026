# K04 — Indexer
Seat: A (teammate) · Depends: K01 · Status: todo
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> i am answer and eval friend is index owner

`data/pages.json` → `data/chroma` with heading-first chunks (ADR-K04) and full metadata
(ADR-K05), plus `data/index_meta.json` for K02. Works before K03 lands: tests use fixture pages.

## Non-negotiables
- Metadata values str or int only. `None` makes Chroma raise.
- One `add_to_store` call path (batched). Never embed one chunk at a time.
- Chunk ids stable: `sha1(url + "#" + position)[:16]`.

## Context (anchors)
- `submission_repo/build/index.py:14` `CHUNK_SIZE, OVERLAP`; `:17` `chunk`; `:33` `build_index` — TODO for `year`, `page_type`.
- `submission_repo/bot/store.py:41` `get_store(reset=True)` deletes `data/chroma`.
- `:82` `add_to_store(store, texts, metadatas, ids, batch_size=128)`.
- REFERENCE § Data contracts — `pages.json` shape, `index_meta.json` shape.

## Steps
- [ ] Tests first, `tests/test_index.py` (use `fake_embed`, `tmp_repo`):
  - `chunk` keeps overlap; no empty chunk; short text → one chunk.
  - `page_chunks(page)`: text starts `"{title} — {heading}\n"`; a section never spills into another.
  - page without `sections` → falls back to `text`, heading `""`.
  - duplicate section body on two pages → indexed once.
  - `page_type("https://x.hk/venues/makerspace-a") == "venues"`; root → `""`.
  - `year`: URL `/events/2025-summer` → `"2025"`; none in URL, title "Awards 2024" → `"2024"`; none → `""`.
  - `build_index(pages)` then `query(get_store(), "<exact chunk text>", k=1)` returns that chunk; metadata keys = the 7 fields.
  - `data/index_meta.json` written with `chunk_size overlap n_chunks n_pages built_at`.
- [ ] Implement `page_type`, `year`, `page_chunks`, dedup, ids, meta file in `build/index.py`.
- [ ] `__main__`: `--chunk-size`, `--overlap` args (defaults 800/100) — K07 sweeps these.
- [ ] Human runs `python -m build.index` (gateway). Print `indexed N chunks`.
- [ ] Commit code. Seat A commits `data/chroma` + `data/index_meta.json` only when K06 records the baseline.

## Definition of done
- Tests green offline. `bot/store.py` unchanged.

## Verification
`cd submission_repo && .venv/bin/python -m pytest -q tests/test_index.py`

Live (human, VPN off, after K03): `.venv/bin/python -m build.index` → `indexed N chunks`;
`cat data/index_meta.json` shows the same N.

## Notes
