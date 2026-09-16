# K05 — Answerer
Seat: B (Ahmet) · Depends: K01 · Status: todo
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> i am answer and eval friend is index owner

`bot/answer.py` becomes the single-shot answerer of ADR-K06 and never raises (ADR-K07). This is
the file that holds the invariant.

## Non-negotiables
- `rag_answer` and `rag_answer_batch` names and signatures unchanged (grader imports them).
- `retrieve` stays a separate function with the same signature (`answer.py:29` docstring).
- Few-shot examples invented. Nothing from `dev_set.json` in the prompt.
- Always answer: a refusal scores 0, a guess may score 0.5 (W0 slide 6).
- `answers[i]` answers `questions[i]`.

## Context (anchors)
- `submission_repo/bot/answer.py:13` `SYSTEM_PROMPT` — role, grounding, format, fallback already there.
- `:24` `CONFIG = {"k": 5}`.
- `:41` `rag_answer` — context joined with `[url]` label only; TODO format check at `:62-63`.
- `:67` `rag_answer_batch` — plain loop; one raise zeroes the batch via `main.py:31-34`.
- `submission_repo/bot/llm.py:63` `chat(..., temperature=0.0, max_tokens=512)`.
- Chunk metadata fields: REFERENCE § Data contracts.

## Steps
- [ ] Tests first, `tests/test_answer.py` (use `fake_chat`, monkeypatch `bot.answer.retrieve`):
  - `clean_answer("How many printers?", "There are 7 printers.") == "7"`.
  - `clean_answer("How many rooms?", "Three.") == "3"`.
  - `clean_answer("Which colour?", "Answer: Blue.\n\nBecause...") == "Blue"`.
  - `clean_answer("How many?", "several")` == `"several"` (no number → raw, not empty).
  - `build_context(chunks)` → blocks `[1] Title — url\n text`, numbered in order.
  - `rag_answer`: user message contains context and question; system is `SYSTEM_PROMPT`.
  - retrieve raises → `chat` still called, with closed-book prompt (no `Context:`), answer returned.
  - `chat` raises once → retried → answer returned; raises twice → `""`, no exception.
  - `rag_answer_batch(["a","b","c"])` with `rag_answer` raising on `"b"` → `[ans_a, "", ans_c]`.
  - `SYSTEM_PROMPT` contains none of the 15 `dev_set.json` answers (lowercased substring check).
- [ ] `SYSTEM_PROMPT`: keep existing four parts; add 3 invented pairs:
      how-many → bare number; name → bare name; date → `D Month YYYY`.
- [ ] `build_context`, `clean_answer` (number words one–twenty), `CLOSED_BOOK_PROMPT`, `_chat_once_retry`.
- [ ] `rag_answer`: try `retrieve` → except → `[]`; empty chunks → closed-book; else context; `clean_answer`.
- [ ] `rag_answer_batch`: per-question try/except → `""`.

## Definition of done
- Tests green offline. `main.py`, `bot/llm.py`, `bot/store.py` unchanged.

## Verification
`cd submission_repo && .venv/bin/python -m pytest -q tests/test_answer.py`

Live (human, VPN off, after K04 live index): `.venv/bin/python main.py "What is the capacity of Makerspace A?"` → one short line.
Without index (`mv data/chroma /tmp/c`): `.venv/bin/python main.py "What does FDM stand for in 3D printing?"` still answers; then `mv /tmp/c data/chroma`.

## Notes
