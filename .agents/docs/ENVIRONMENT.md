# Environment — gateway, keys, traps

Facts about running the bot. Repo-visible on purpose: no team fact lives only in one
person's local agent memory.

## Gateway

Azure APIM in front of Azure OpenAI. Three deployments, three URLs, built in `bot/llm.py`
from `.env`:

| Call | URL shape |
|---|---|
| chat | `{AZURE_CHAT_BASE}/deployments/{CHAT_DEPLOYMENT}/chat/completions?api-version={API_VERSION}` |
| vision | `{AZURE_CHAT_BASE}/deployments/{VISION_DEPLOYMENT}/chat/completions?api-version={API_VERSION}` |
| embed | `{AZURE_EMBED_BASE}/openai/deployments/{EMBED_DEPLOYMENT}/embeddings?api-version={API_VERSION}` |

Chat route has no `/openai` segment, embed route does. Asymmetry is real. Match them and one 404s.

Key is an APIM subscription key (32 chars), sent as `api-key`. `.env` is gitignored — a
committed key gets rotated and every submission using it stops working.

## TRAP: VPN gives 403 Forbidden (2026-09-16)

`check_setup.py` fails both live calls with `403 - {'statusCode': 403, 'message': 'Forbidden'}`
when a consumer VPN is on. Key is fine; gateway policy rejects the exit IP.

Distinguishing 403 from a bad key — same chat URL, three requests:

| `api-key` header | Response |
|---|---|
| absent | `401 ... missing subscription key` |
| bogus 32 chars | `401 ... invalid subscription key` |
| real key, VPN on | `403 Forbidden` |

So: **401 = key problem. 403 = network/policy problem, key already authenticated.**

Fix: VPN off, rerun. Still 403 off-VPN means the key's product subscription or an IP
allowlist, which is an organizer question, not a code change.

## Running

```bash
cd submission_repo
.venv/bin/python check_setup.py            # want: READY
.venv/bin/python main.py "your question"   # grader's command
```

Anything importing `bot.llm` (`check_setup.py`, `main.py`, the Lab notebooks) hits the
gateway and needs VPN off.
