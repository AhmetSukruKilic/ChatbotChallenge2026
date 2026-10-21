# K06 — Baseline run
Seat: B (Ahmet) · Depends: K02, K03, K04, K05 · Status: todo
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> how should we plan our rag what do you think I dont wanna blindly develop it

First real number, on the live gateway. Every later change is measured against this row.
Rewritten 2026-10-21 for solo + prelim (ADR-K12, ADR-K13): Ahmet runs and commits everything.

## Non-negotiables
- Defaults only: chunks as `build/index.py` ships, `CONFIG` as `bot/answer.py` ships. Tuning = K07.
- Gateway commands run by Ahmet, VPN off (ADR-K11).
- `main.py`, `bot/llm.py`, `bot/store.py`, `check_setup.py` unchanged.

## Context (anchors)
- REFERENCE § Commands — exact sequence.
- `submission_repo/data/pages.json`, `data/images.json` — committed by K03.
- `submission_repo/eval/experiment_log.csv` — created by first `build.evaluate` run.
- Image descriptions are K08; baseline runs without them (Lv3 near 0 expected).

## Files touched
- `submission_repo/data/chroma/` (generated), `submission_repo/eval/experiment_log.csv`, this file.

## Steps
- [ ] `.venv/bin/python check_setup.py` → `READY`.
- [ ] `.venv/bin/python -m build.index` → `indexed 6421 text chunks, N image chunks (0 described)`.
- [ ] `.venv/bin/python -m build.evaluate --note "baseline"`; paste output.
- [ ] Classify each miss in `## Notes`: `retrieval` (miss) / `prompt` (HIT, score < 1) / `image` / `reasoning`.
- [ ] `time .venv/bin/python main.py "What does FDM stand for in 3D printing?"` → one line, < 30s.
- [ ] Batch timing: `time .venv/bin/python main.py "q1" "q2" "q3" "q4" "q5"` → 5 lines.
- [ ] Commit `eval/experiment_log.csv` + `data/chroma`.

## Definition of done
- One `baseline` row; Lv1 > 0 and Lv2 > 0; slowest < 30s.

## Verification
`cd submission_repo && .venv/bin/python -c "import csv;r=[x for x in csv.DictReader(open('eval/experiment_log.csv')) if x['note']=='baseline'][-1];print(r);assert float(r['slowest_s'])<30 and 'L1=0/' not in r['per_level'] and 'L2=0/' not in r['per_level']"`

## Notes
