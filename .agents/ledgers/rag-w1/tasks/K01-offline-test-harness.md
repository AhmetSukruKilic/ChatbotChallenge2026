# K01 — Offline test harness
Seat: B (Ahmet) · Depends: — · Status: todo
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> how should we plan our rag what do you think I dont wanna blindly develop it

Every later task proves itself with pytest, without the gateway (ADR-K10). This task gives them
the fakes and the runner. No product code changes.

## Non-negotiables
- No test may open a network socket. Agents run these behind a VPN that 403s the gateway.
- `requirements.txt` unchanged — the grader installs it; pytest is dev-only.

## Context (anchors)
- `submission_repo/bot/store.py:13` — `from bot.llm import embed`; name bound in `bot.store`.
- `submission_repo/bot/answer.py:7` — `from bot.llm import chat`; name bound in `bot.answer`.
- `submission_repo/bot/store.py:15` — `DEFAULT_PATH = "data/chroma"`, relative to cwd.
- `submission_repo/bot/llm.py:40` — `_KEY` read at import; empty key only fails on first real call, so importing is safe.

## Steps
- [ ] Create `submission_repo/requirements-dev.txt`: `-r requirements.txt` and `pytest>=8`.
- [ ] Install: `.venv/bin/pip install -r requirements-dev.txt`.
- [ ] Create `submission_repo/pytest.ini`: `testpaths = tests`, `pythonpath = .`.
- [ ] Create `submission_repo/tests/__init__.py` (empty) and `tests/fixtures/.fixtureshere`.
- [ ] `tests/conftest.py`, fixtures per REFERENCE § Test conventions:
  - `fake_embed(monkeypatch)` — `vec(t)` = first 16 bytes of `sha256(t)` scaled to [0,1]; patches
    `bot.store.embed` with `lambda texts: [vec(t) for t in texts]`; returns `vec`.
  - `fake_chat(monkeypatch)` — object with `.replies` (list, popped front; default `"ok"`),
    `.calls` (list of messages lists), `.fail_times` (int; raise `RuntimeError` that many times
    first); patches `bot.answer.chat`.
  - `tmp_repo(tmp_path, monkeypatch)` — `monkeypatch.chdir(tmp_path)`, creates `data/`, returns `tmp_path`.
  - autouse: `monkeypatch.setenv("ANONYMIZED_TELEMETRY", "False")` — Chroma telemetry must not trip `no_network`.
  - `no_network` autouse — patches `socket.socket.connect` to raise `RuntimeError("network in test")`.
- [ ] `tests/test_harness.py`: `fake_embed` deterministic (same text → same vector, different
      text → different vector); `get_store()` + `add_to_store` + `query` round-trip in `tmp_repo`
      returns the exact inserted text first; `no_network` raises on `socket.create_connection(("127.0.0.1", 9))`.
- [ ] `submission_repo/.gitignore`: add `.pytest_cache/`, `eval/failures.json`, `data/_tmp_image`.

## Definition of done
- `pytest -q` green offline, 3+ tests.
- `requirements.txt`, `bot/`, `main.py` byte-for-byte unchanged.

## Verification
`cd submission_repo && .venv/bin/python -m pytest -q`

Expect `N passed`, N ≥ 3. Then `git diff --stat -- requirements.txt bot main.py` prints nothing.

## Notes
