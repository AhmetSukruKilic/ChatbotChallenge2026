# RAG W1 — Execution Prompt

Paste verbatim for each session. One session = one task. Session has no memory — everything
lives in this folder.

> Please execute @.agents/ledgers/rag-w1/EXECUTION_PROMPT.md. I am <Ahmet|teammate>.

---

## Prompt (copy from here down)

You are executing one task from the RAG W1 ledger in `.agents/ledgers/rag-w1/`. Follow in order.

1. **Who you are.** The invocation names the person. Not named → stop and ask.

   | Seat | Person | Tasks |
   |---|---|---|
   | A — index owner | teammate | K03, K04, K06 |
   | B — answer + eval | Ahmet | K01, K02, K05, K07 |

   Never work a task this table does not give you.
2. **Preflight.** `git pull --rebase origin main`. `git status --porcelain` not empty → stop, report.
3. **Read `STATE.md` in full.**
4. **Pick the task.** Yours and `in_progress` → resume. Else first row that is yours, `todo`,
   every `Depends on` `done`. Nothing eligible → print `BLOCKED <your ID> needs <ID> (<status>)`
   and stop.
5. **Read `REFERENCE.md` once.** Then only your task file.
6. **Do the work.** Tick `## Steps`. Test red before implementation. Stay in scope; adjacent
   ideas go to STATE.md Backlog.
7. **Run `## Verification` verbatim.** Fails → fix code, never the command. Gateway commands:
   print them for the human, wait for pasted output (ADR-K11).
8. **Close.** Fill `## Notes` (≤ 40 lines). Ledger row → `done`. Repoint "Current task".
   Rewrite "Last session ended" (≤ 8 lines, prior entry kept as `Prior:`).
9. **Commit + push** to `main`: `type(ID): title`. No AI attribution. Seat B never stages
   `submission_repo/data/chroma`.
10. **STOP.** Next task = next session.

### Blocked mid-task

Row → `blocked`. Write it in STATE.md `## Open blockers`: what, who provides it, which IDs it
unblocks. Commit, push, stop.

### Guardrails

- Invariant: `main.py "q"` → one short answer, < 30s, never raises. Anything threatening it stops the task.
- Never edit `main.py`, `bot/llm.py`, `bot/store.py`, `check_setup.py`.
- Never call the gateway yourself. Never guess keys, URLs, deployment names.
- Never use `dev_set.json` answers in prompts.
- Renumber nothing. Past ADRs never edited — supersede with a new one.
