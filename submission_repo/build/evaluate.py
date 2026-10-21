"""Score the bot on a question set. Calls the gateway: run it yourself.

    python -m build.evaluate                       # dev_set.json
    python -m build.evaluate --set my_set.json --note "k 8 -> 10"

Per question: retrieval hit (are the expected answer's words in the
retrieved chunks?), a proxy answer score (1 / 0.5 / 0, the judges are
human), and time. Appends one row to eval/experiment_log.csv and writes
the misses to eval/failures.json. Lv5 needs our own photos and Lv4 is
reasoning, so read those rows rather than trusting the hit column.
"""
import argparse
import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path

from bot import answer as bot

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "eval"

STOP = {"a", "an", "the", "of", "and", "in", "on", "to", "for", "is", "at"}


def tokens(s: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", str(s).lower())
    return [w for w in words if w not in STOP] or words


def score(expected: str, got: str) -> float:
    exp, out = tokens(expected), tokens(got)
    if not out:
        return 0.0
    if exp == out:
        return 1.0
    present = sum(t in out for t in exp)
    if present == len(exp) and len(out) <= 3 * len(exp) + 2:
        return 1.0
    return 0.5 if present * 2 >= len(exp) else 0.0


def hit(expected: str, chunks: list[dict]) -> bool:
    joined = set(tokens(" ".join(c["text"] for c in chunks)))
    return all(t in joined for t in tokens(expected))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default=str(ROOT / "dev_set.json"))
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    items = json.loads(Path(args.set).read_text())
    rows, failures = [], []
    for it in items:
        q, exp = it["question"], it["answer"]
        t0 = time.time()
        try:
            vec = bot._embed([q], t0 + bot.CONFIG["budget_s"])[0]
            chunks = bot.retrieve_vec(vec)
        except Exception as exc:                  # noqa: BLE001
            print("retrieval error:", exc)
            vec, chunks = None, []
        got = bot._answer(q, vec, t0)
        secs = time.time() - t0
        s, h = score(exp, got), hit(exp, chunks)
        rows.append({"level": it.get("level", 0), "score": s, "hit": h, "secs": secs})
        print(f"L{it.get('level', '?')} {s:>3} {'HIT ' if h else 'miss'} {secs:5.1f}s  "
              f"{q[:60]!r}\n        want {exp!r}\n        got  {got!r}")
        if s < 1:
            failures.append({**it, "got": got, "hit": h, "secs": round(secs, 1),
                             "top": [f"{c['metadata'].get('kind')} {c['distance']:.3f} "
                                     f"{c['metadata'].get('url')}" for c in chunks[:5]]})

    levels = sorted({r["level"] for r in rows})
    per_level = {lv: sum(r["score"] for r in rows if r["level"] == lv) for lv in levels}
    counts = {lv: sum(r["level"] == lv for r in rows) for lv in levels}
    total = sum(r["score"] for r in rows)
    hits = sum(r["hit"] for r in rows)
    slowest = max(r["secs"] for r in rows)
    mean = sum(r["secs"] for r in rows) / len(rows)

    print("\n" + "  ".join(f"Lv{lv} {per_level[lv]:g}/{counts[lv]}" for lv in levels))
    print(f"total {total:g}/{len(rows)}  retrieval {hits}/{len(rows)}  "
          f"mean {mean:.1f}s  slowest {slowest:.1f}s")

    EVAL.mkdir(exist_ok=True)
    log = EVAL / "experiment_log.csv"
    new = not log.exists()
    with log.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "note", "set", "k", "k_image", "total", "n", "retrieved",
                        "per_level", "mean_s", "slowest_s"])
        w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), args.note, Path(args.set).name,
                    bot.CONFIG["k"], bot.CONFIG["k_image"], total, len(rows), hits,
                    " ".join(f"L{lv}={per_level[lv]:g}/{counts[lv]}" for lv in levels),
                    f"{mean:.1f}", f"{slowest:.1f}"])
    (EVAL / "failures.json").write_text(json.dumps(failures, indent=1, ensure_ascii=False))
    print(f"logged to {log}, {len(failures)} misses in eval/failures.json")


if __name__ == "__main__":
    main()
