# K02 — Eval script
Seat: B (Ahmet) · Depends: K01 · Status: todo
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> how should we plan our rag what do you think I dont wanna blindly develop it

W1 method: change one setting, re-score, keep it if the number rose (ADR-K08). This script is
the "re-score". Retrieval-hit and answer score stay separate: hit without score = prompt problem,
no hit = retrieval problem.

## Non-negotiables
- Scoring is a proxy (PLAN § Scoring proxy). Print it as such; never call it the judge's score.
- Append-only log. Never rewrite or truncate `eval/experiment_log.csv`.
- Pure functions tested offline; `main()` is the only part touching the gateway.

## Context (anchors)
- `submission_repo/dev_set.json` — 15 `{level, question, answer}`.
- `submission_repo/bot/answer.py:29` `retrieve`, `:41` `rag_answer`, `:24` `CONFIG["k"]`.
- `data/index_meta.json` — K04 writes it; may be missing → blank `chunk_size`/`overlap`.
- REFERENCE § Data contracts — CSV header, exact order.
- `submission_repo/build/__init__.py` exists → `python -m build.evaluate` works.

## Definitions
- `normalize(s)`: lowercase, punctuation → space, collapse spaces, drop tokens `a an the`.
- content tokens: `normalize(s).split()` minus `and or of`.
- `score_answer(expected, answer)`: 1 if normalized equal, or every expected content token in answer tokens and
  `len(answer tokens) <= 3 * len(expected tokens)`; else 0.5 if ≥ half the expected content tokens present; else 0.
- `retrieval_hit(expected, chunks)`: every expected content token in `normalize(" ".join(c["text"] for c in chunks))`.

## Steps
- [ ] Tests first, `tests/test_evaluate.py`, all red before code:
  - `normalize("The Faculty of Engineering.") == "faculty of engineering"`.
  - `score_answer("Additive manufacturing", "additive manufacturing") == 1`.
  - `score_answer("PVC and polycarbonate", "Polycarbonate and PVC") == 1`.
  - `score_answer("Tidewatch, Loomstack and Pathfinder", "Tidewatch") == 0` (1 of 3 < half).
  - `score_answer("Tidewatch, Loomstack and Pathfinder", "Tidewatch and Loomstack") == 0.5`.
  - `score_answer("40", "40 people")` == 1; `score_answer("40", "")` == 0.
  - verbose: `score_answer("Blue", "<30-word sentence containing blue>") == 0.5` (> 3× length).
  - `retrieval_hit("17 October 2025", [{"text": "deadline 17 october 2025"}]) is True`; missing token → False.
  - `run(entries, answer_fn, retrieve_fn)` with fakes: per-level sums, `over_30s` counted from an
    injected clock, answer_fn raising → answer `""`, score 0, run continues.
  - `append_row(path, row)` creates header once, appends on second call, column order = REFERENCE.
- [ ] `build/evaluate.py`: `normalize`, `score_answer`, `retrieval_hit`, `run(entries, answer_fn, retrieve_fn, clock=time.perf_counter)`, `append_row`, `main()`.
- [ ] `main()` argparse: `--change` (required), `--who` (required), `--dataset` (default `dev_set.json`).
      Calls `run(load(dataset), rag_answer, retrieve)`; k from `CONFIG`; chunk settings from `data/index_meta.json`.
- [ ] Output: one line per question `L{level} {hit:Y/N} {score} {secs}s  Q → A (expected E)`; then totals
      `retrieved x/15  score y/15  L1..L5  mean  slowest`; then `PROXY SCORE — read eval/failures.json`.
- [ ] Write `eval/failures.json`: every entry with score < 1, fields `level question expected answer hit top_urls`.
- [ ] Append CSV row to `eval/experiment_log.csv` (create `eval/`).

## Definition of done
- All listed tests green offline.
- Gateway command documented in REFERENCE works unchanged: `python -m build.evaluate --change ... --who ...`.

## Verification
`cd submission_repo && .venv/bin/python -m pytest -q tests/test_evaluate.py`

Live (human, after K04+K05, VPN off): `.venv/bin/python -m build.evaluate --change "smoke" --who ahmet`
→ 15 lines + totals; `eval/experiment_log.csv` gains one row. Delete that smoke row before K06 commits.

## Notes
