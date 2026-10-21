# K09 — Prelim submission package
Seat: B (Ahmet) · Depends: K06 · Status: blocked (Codabench format)
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> because i need to connect to school network i need to run by myself what do i need for submission

Get `submission_repo/` onto Codabench by the 21 Oct deadline (W0 slide 2: code and vector
database), reproducible on the grader (W0 slide 8: pin, clean venv).

## Non-negotiables
- `.env` never committed, never zipped (root `.gitignore` ignores `*.zip` for this reason).
- `data/chroma` committed (`submission_repo/.gitignore` note: grader only has what is committed).
- Grader runs `python main.py "q"` read-only; `bot/store.py` copies the index to temp when needed.

## Context (anchors)
- `submission_repo/requirements.txt` — pinned 2026-10-21 (openai 3.14.0, chromadb 1.5.9, bs4 4.15.0,
  requests 2.34.2, python-dotenv 1.2.3).
- `submission_repo/bot/answer.py` `STORE_PATH` absolute from `__file__` — cwd does not matter.
- Unknown: Codabench upload format (zip of `submission_repo/`? repo link?) and how the grader
  supplies the gateway key. STATE.md Open blockers.

## Files touched
- None in code. Possibly a zip outside the repo.

## Steps
- [ ] Owner confirms upload format + key handling (blocker).
- [ ] Clean venv: `python3 -m venv /tmp/cv && /tmp/cv/bin/pip install -r requirements.txt`.
- [ ] Copy `.env` in, then `/tmp/cv/bin/python main.py "What does FDM stand for in 3D printing?"` → one line.
- [ ] Read-only test: `chmod -R a-w data/chroma`, run one question, `chmod -R u+w data/chroma`.
- [ ] Package per Codabench instructions, excluding `.env`, `.venv`, `__pycache__`, `eval/failures.json`.
      Zip: `zip -r ../submission.zip . -x '.env' '.venv/*' '*__pycache__*'` then `unzip -l` it, grep for `.env`.
- [ ] Upload. Record leaderboard result in `## Notes`.

## Definition of done
- Submission accepted by Codabench; result in Notes.

## Verification
`unzip -l ../submission.zip | grep -E '\.env$|\.venv/' ; test $? -eq 1 && echo CLEAN`

## Notes
