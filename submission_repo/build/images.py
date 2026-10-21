"""Image pipeline. Workshop 2 blocks 2 and 3.

Describes every image in data/images.json once with the vision model and
caches the result in data/descriptions.json, keyed by image URL. Safe to
stop and rerun: described images are skipped, failures are retried.
Rebuilds the index at the end so the descriptions are searchable.

    python -m build.images                 # describe all, then rebuild index
    python -m build.images --limit 50      # try a few first
    python -m build.images --no-index      # describe only

Never describe an image while answering a question. Ingestion time is
unlimited; runtime is 30 seconds.
"""
import argparse
import base64
import json
import mimetypes
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from bot.llm import CHAT_DEPLOYMENT, CHAT_URL, VISION_DEPLOYMENT, VISION_URL, _client

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE_PATH = DATA / "descriptions.json"

MAX_BYTES = 15 * 1024 * 1024

DESCRIPTION_PROMPT = """You are building a searchable record of an image from the website of
the Tam Wing Fan Innovation Wing / Innovation Academy (Faculty of Engineering, HKU).
The record is the only way anyone can answer questions about this image later.
Anything you leave out is lost.

Context from the web page (may be empty): {context}

Write these sections, in this order:
1. TYPE: photo, poster, flyer, certificate, diagram, chart, screenshot or other.
2. LOCATION / SUBJECT: the room, area, event or project, as any sign or text names it.
3. VISIBLE TEXT: every word of text in the image, copied exactly as written,
   line by line, including titles, names, team names, dates, times, venues,
   prices, numbers, awards, slogans and small print. Do not summarise or translate.
   Write [unreadable] for text you cannot make out.
4. OBJECTS WITH COUNTS: every distinct kind of object, with an exact count
   ("11 tables", "4 3D printers"), never "some" or "several". Count people too.
5. LAYOUT: what is next to, behind, above or facing what.
6. COLOURS AND MATERIALS: only where they identify something specific.

Do not add anything that is not visible. Do not describe the mood."""

_lock = threading.Lock()


def _ask_vision(url: str, deployment: str, prompt: str, data: bytes, mime: str) -> str:
    """One vision call. gpt-5-mini is a reasoning model, so it needs
    max_completion_tokens with room for reasoning; older deployments
    take the plain call."""
    b64 = base64.b64encode(data).decode()
    messages = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
    ]}]
    client = _client(url)
    try:
        r = client.chat.completions.create(
            model=deployment, messages=messages,
            max_completion_tokens=6000, reasoning_effort="low", timeout=120,
        )
    except Exception as exc:                      # noqa: BLE001
        if "400" not in str(exc):
            raise
        r = client.chat.completions.create(model=deployment, messages=messages, timeout=120)
    return (r.choices[0].message.content or "").strip()


def _context(im: dict) -> str:
    bits = [f"page title: {im.get('page_title', '')}"]
    if im.get("alt"):
        bits.append(f"alt text: {im['alt']}")
    if im.get("caption"):
        bits.append(f"caption: {im['caption']}")
    return "; ".join(bits)


def describe_one(im: dict, url: str, deployment: str) -> str:
    resp = requests.get(im["src"], timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    if len(resp.content) > MAX_BYTES:
        raise ValueError(f"{len(resp.content) // 1024} KB, too large")
    mime = resp.headers.get("content-type", "").split(";")[0]
    if not mime.startswith("image/"):
        mime = mimetypes.guess_type(im["src"].split("?")[0])[0] or "image/jpeg"
    return _ask_vision(url, deployment, DESCRIPTION_PROMPT.format(context=_context(im)),
                       resp.content, mime)


HIGH_VALUE = re.compile(r"\b(posters?|flyers?|awards?|winners?|champions?|prizes?|maps?|floor ?plans?|"
                        r"venues?|rooms?|makerspace|schedule|rundown|programme|timetable|signs?|"
                        r"signage|leaflet|infographic)\b", re.I)


def priority(im: dict) -> int:
    """Higher first. Text-heavy images (posters, maps) and recent years
    are the likeliest Lv3 sources, so --limit spends the budget there."""
    hay = f"{im['src']} {im.get('alt', '')} {im.get('caption', '')} {im.get('page_title', '')}"
    year = re.search(r"/uploads/(20\d\d)/", im["src"])
    year = int(year.group(1)) if year else 0
    return (3 * bool(HIGH_VALUE.search(hay))
            + (2 if year >= 2025 else 1 if year == 2024 else 0)
            + im["src"].lower().endswith(".png")
            + bool(im.get("caption")))


def describe_all(images: list[dict], workers: int = 6, limit: int = None,
                 use_chat_model: bool = False) -> dict:
    cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
    url, deployment = (CHAT_URL, CHAT_DEPLOYMENT) if use_chat_model else (VISION_URL, VISION_DEPLOYMENT)
    todo = sorted((im for im in images if not cache.get(im["src"])), key=priority, reverse=True)
    if limit:
        todo = todo[:limit]
    print(f"{len(cache)} cached, {len(todo)} to describe with {deployment}")

    def save():
        DATA.mkdir(exist_ok=True)
        tmp = CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
        tmp.replace(CACHE_PATH)

    started, done, failed = time.time(), 0, 0
    with ThreadPoolExecutor(workers) as pool:
        futures = {pool.submit(describe_one, im, url, deployment): im for im in todo}
        for fut in as_completed(futures):
            im = futures[fut]
            try:
                text = fut.result()
                with _lock:
                    if text:
                        cache[im["src"]] = text
                        done += 1
                    else:
                        failed += 1
                        print("empty:", im["src"][-70:])
            except Exception as exc:              # noqa: BLE001
                failed += 1
                print("failed:", im["src"][-70:], type(exc).__name__, str(exc)[:120])
            if (done + failed) % 20 == 0:
                with _lock:
                    save()
                rate = (done + failed) / (time.time() - started)
                print(f"  {done + failed}/{len(todo)}  ({rate:.2f}/s, {failed} failed)")
    save()
    print(f"{done} described, {failed} failed, {len(cache)} cached in total")
    return cache


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--chat-model", action="store_true",
                    help="describe with the chat deployment (gpt-4o-mini) instead of gpt-5-mini")
    ap.add_argument("--no-index", action="store_true")
    args = ap.parse_args()

    images = json.loads((DATA / "images.json").read_text())
    describe_all(images, workers=args.workers, limit=args.limit, use_chat_model=args.chat_model)
    if not args.no_index:
        from build.index import build_index
        build_index()
