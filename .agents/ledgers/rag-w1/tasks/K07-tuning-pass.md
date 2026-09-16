# K07 — Tuning pass
Seat: B (Ahmet) · Depends: K06 · Status: todo
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> how should we plan our rag what do you think I dont wanna blindly develop it

One setting at a time against the K06 baseline (W1 block 5). Keep a change only if `score` rises,
or `retrieved` rises and `score` holds.

## Non-negotiables
- One change per row. Two changes in one row = unreadable delta.
- Local `data/chroma` rebuilds are fine; never stage `data/chroma` (seat A only, ADR-K09).
- Each run is a gateway command → human runs it (ADR-K11).
- Any row with `over_30s > 0` is rejected regardless of score.

## Context (anchors)
- `submission_repo/bot/answer.py:24` `CONFIG["k"]` — no rebuild needed.
- `submission_repo/build/index.py` `--chunk-size`, `--overlap` (K04) — rebuild needed.
- `eval/experiment_log.csv` — baseline row from K06.

## Steps
- [ ] k sweep, no rebuild, one row each: k = 3, 8, 10. `--change "k 5->N"`.
- [ ] Set `CONFIG["k"]` to the best k.
- [ ] Chunk sweep at best k, rebuild each: `python -m build.index --chunk-size S --overlap O`
      for (500,75), (1200,150). `--change "chunk 800->S"`.
- [ ] Rebuild with the best chunk settings; set `CHUNK_SIZE, OVERLAP` defaults in `build/index.py` to match.
- [ ] One prompt change only if failures show `prompt` class (hit Y, score < 1): name it in `--change`.
- [ ] `## Notes`: table of all rows, the kept settings, and the top 3 remaining failure classes.
- [ ] Ask seat A to rebuild + commit `data/chroma` with the kept settings.

## Definition of done
- ≥ 5 new rows in `eval/experiment_log.csv`.
- Kept settings in code; best row's `score` ≥ baseline `score`.

## Verification
`cd submission_repo && .venv/bin/python -c "import csv;rows=list(csv.DictReader(open('eval/experiment_log.csv')));b=[r for r in rows if r['change']=='baseline'][-1];print(len(rows),'rows');assert len(rows)>=6 and max(float(r['score']) for r in rows)>=float(b['score'])"`

## Notes
