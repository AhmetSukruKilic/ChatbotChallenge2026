# K07 — Tuning pass
Seat: B (Ahmet) · Depends: K06 · Status: todo
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> how should we plan our rag what do you think I dont wanna blindly develop it

One setting at a time against the K06 baseline (W1 block 5). Keep a change only if `score` rises,
or `retrieved` rises and `score` holds.

## Non-negotiables
- Deadline day (ADR-K12): K09 submission first; this task only with time left.
- One change per row. Two changes in one row = unreadable delta.
- Rebuild + commit `data/chroma` with the kept settings (ADR-K13).
- Each run is a gateway command → human runs it (ADR-K11).
- Any row with `slowest_s >= 30` is rejected regardless of score.

## Context (anchors)
- `submission_repo/bot/answer.py` `CONFIG` — `k`, `k_image`; no rebuild needed.
- `submission_repo/build/index.py` `CHUNK_SIZE, OVERLAP`, `SECTION_MAX` — edit constants, rebuild (no CLI args, K04 Notes).
- `eval/experiment_log.csv` — baseline row from K06.

## Files touched
- `submission_repo/bot/answer.py`, `submission_repo/build/index.py`, `submission_repo/data/chroma/`, `submission_repo/eval/experiment_log.csv`.

## Steps
- [ ] k sweep, no rebuild, one row each: k = 5, 10, 12. `--note "k 8->N"`.
- [ ] Set `CONFIG["k"]` to the best k.
- [ ] Chunk sweep at best k, rebuild each: (500,75), (1200,150). `--note "chunk 800->S"`.
- [ ] Rebuild with the best chunk settings; set `CHUNK_SIZE, OVERLAP` defaults in `build/index.py` to match.
- [ ] One prompt change only if failures show `prompt` class (hit Y, score < 1): name it in `--note`.
- [ ] `## Notes`: table of all rows, the kept settings, and the top 3 remaining failure classes.
- [ ] Rebuild + commit `data/chroma` with the kept settings.

## Definition of done
- ≥ 5 new rows in `eval/experiment_log.csv`.
- Kept settings in code; best row's `score` ≥ baseline `score`.

## Verification
`cd submission_repo && .venv/bin/python -c "import csv;rows=list(csv.DictReader(open('eval/experiment_log.csv')));b=[r for r in rows if r['note']=='baseline'][-1];print(len(rows),'rows');assert len(rows)>=6 and max(float(r['total']) for r in rows)>=float(b['total'])"`

## Notes
