# K06 — Baseline run
Seat: A (teammate) · Depends: K02, K03, K04, K05 · Status: todo
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> how should we plan our rag what do you think I dont wanna blindly develop it

First real number. Every later change is measured against this row. W1 deadline check: Lv1 and
Lv2 above zero (ADR-K01).

## Non-negotiables
- Default settings only: chunk 800/100, k 5. No tuning in this task — that is K07.
- Gateway commands run by a human (ADR-K11).
- Seat A is the only one who commits `data/chroma` (ADR-K09).

## Context (anchors)
- REFERENCE § Commands — the exact sequence.
- `submission_repo/eval/experiment_log.csv` — K02 created the header.
- `submission_repo/eval/failures.json` — read, not committed.

## Steps
- [ ] `git pull`; confirm `data/pages.json` from K03 present.
- [ ] Human, VPN off: `.venv/bin/python check_setup.py` → `READY`.
- [ ] Human: `.venv/bin/python -m build.index` → `indexed N chunks`.
- [ ] Human: `.venv/bin/python -m build.evaluate --change "baseline" --who <name>`; paste full output.
- [ ] Read every failure. Classify each in `## Notes`: `retrieval` (hit N) / `prompt` (hit Y, score < 1) / `image` (Lv3, Lv5 — expected 0) / `reasoning` (Lv4).
- [ ] Time one single question: `time .venv/bin/python main.py "<a Lv2 question>"` — under 30s.
- [ ] Commit `eval/experiment_log.csv`, `data/chroma`, `data/index_meta.json`.

## Definition of done
- One `baseline` row in `eval/experiment_log.csv`, `L1 > 0` and `L2 > 0`.
- Failure classification in `## Notes`.
- If L1 or L2 is 0: row `blocked`, STATE.md `## Open blockers` names the failing class.

## Verification
`cd submission_repo && .venv/bin/python -c "import csv;r=[x for x in csv.DictReader(open('eval/experiment_log.csv')) if x['change']=='baseline'][-1];print(r);assert float(r['L1'])>0 and float(r['L2'])>0"`

## Notes
