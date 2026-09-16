# ChatbotChallenge2026

RAG chatbot about the Tam Wing Fan Innovation Wing. Submission is `submission_repo/`;
everything else is workshop material.

This file holds only what the repo cannot tell you itself. Structure follows the `.agents/`
convention from Group-6 (Interviewly).

## Layout

| Path | What |
|---|---|
| `submission_repo/` | The entry. `main.py` + `bot/` + `build/`. What gets graded. |
| `Labs/` | Workshop notebooks `lab1`–`lab5`. Practice, not submission. |
| `Slides/` | W0 setup/rules, W1 RAG pipeline, W2 visual & physical data. |
| `deprecated/` | Old monolithic prototype. Reference only, do not build on it. |
| `.agents/` | Team memory — docs, specs, features, ledgers, devlogs, prompts. |

## Given vs yours

Given, do not edit: `submission_repo/main.py`, `bot/llm.py`, `bot/store.py`, `check_setup.py`.
The grading harness runs `main.py` exactly as it is.

Yours: `bot/answer.py` (`rag_answer`, `rag_answer_batch`) and everything under `build/`.

## Running

```bash
cd submission_repo
.venv/bin/python check_setup.py            # want: READY
.venv/bin/python main.py "your question"   # grader's command
```

**VPN on = every gateway call 403s.** Key is fine, exit IP is not. Full evidence and the
401-vs-403 test in [`.agents/docs/ENVIRONMENT.md`](.agents/docs/ENVIRONMENT.md).

Grader budget: 30s per question (`TIME_LIMIT` in `main.py`). `bot.llm.embed` takes a list —
batch it; one call per string is minutes of round trips.

## Working rules

- **No team fact lives only in local agent memory.** Anything a teammate would need goes in
  `.agents/` and gets committed. Local memory holds pointers, nothing else.
- Docs terse: drop articles and hedging, bullets over prose, tables over bullets. Keep the
  search keys exact — file, symbol, error code, ID.
- One home per fact, referenced elsewhere by name. Never explain the same thing twice.
- Agents commit and push here; no approval round-trip. PRs stay human.
- No AI attribution anywhere: no `Co-Authored-By` trailer on commits, no "Generated with"
  line in PR descriptions.
- Agents do not run anything that calls the gateway — a human runs those (VPN, see below).
- Never guess credentials, deployment names or gateway config.

## `.agents/`

| Dir | Holds |
|---|---|
| `docs/` | Durable repo knowledge. Environment, traps, idea. |
| `specs/` | Dated design specs, `YYYY-MM-DD-<topic>.md`. |
| `features/` | Acceptance criteria as `.feature` files. |
| `ledgers/<area>/` | `PLAN.md` `STATE.md` `DECISIONS.md` `REFERENCE.md` `MODELS.md` `tasks/`. |
| `devlogs/` | One per finished task, `<TASK-ID>-<slug>.md`, written in the session that did it. |
| `prompts/` | Reusable prompts. |

Ledgers are empty until the team splits the work into owned task IDs.
