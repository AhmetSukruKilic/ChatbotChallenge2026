# K08 — Image descriptions run
Seat: B (Ahmet) · Depends: K03, K04 · Status: todo
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> yes do then update we are alone no need for teammates

Lv3 is 40% of the prelim (ADR-K12). Describe as many high-priority images as time allows,
cache them, rebuild the index with them (ADR-K15).

## Non-negotiables
- Never describe at query time. Build step only.
- `data/descriptions.json` is the cache: never delete it; reruns skip what it holds.
- Gateway: Ahmet runs, VPN off (ADR-K11).

## Context (anchors)
- `submission_repo/build/images.py` `DESCRIPTION_PROMPT`, `priority()`, `describe_all()`, `_ask_vision()`.
- `_ask_vision` tries `max_completion_tokens` + `reasoning_effort="low"`, falls back to a plain
  call on any 400. Untested live.
- 5247 images; priority ≥ 3: 1167; ≥ 4: 437.
- `submission_repo/build/index.py` `image_chunks()` — rebuild runs automatically at the end.

## Files touched
- `submission_repo/data/descriptions.json` (new, committed), `submission_repo/data/chroma/`, this file.

## Steps
- [ ] Probe: `.venv/bin/python -m build.images --limit 12 --no-index`. Note the `/s` rate and failures.
- [ ] Read 3 entries of `data/descriptions.json`: verbatim text present? counts present?
      Empty or reasoning-truncated → try `--chat-model` on the probe and compare.
- [ ] Size the run: N = rate × seconds available. `.venv/bin/python -m build.images --limit N`.
      Interrupt is safe; rerun resumes.
- [ ] Ends with `indexed … (M described)`. Re-run `build.evaluate --note "images M"`.
- [ ] Commit `data/descriptions.json` + `data/chroma`.

## Definition of done
- ≥ 400 images described, index rebuilt, one `images` row in `eval/experiment_log.csv`.

## Verification
`cd submission_repo && .venv/bin/python -c "import json;d=json.load(open('data/descriptions.json'));print(len(d));assert len(d)>=400"`

## Notes
