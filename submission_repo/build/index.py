"""Indexer. Workshop 1 block 4.

Builds data/chroma from scratch: text chunks from data/pages.json plus
one chunk per image from data/images.json, using the cached vision
descriptions in data/descriptions.json where they exist. Rerun it after
build/images.py adds descriptions; nothing is described here.

    python -m build.index
"""
import hashlib
import json
import re
import shutil
from pathlib import Path

from bot.store import add_to_store, get_store

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STORE_PATH = str(DATA / "chroma")

CHUNK_SIZE, OVERLAP = 800, 100
SECTION_MAX = 1000       # a section up to this size stays one chunk
IMAGE_TEXT_MAX = 6000


def sections(text: str) -> list[tuple[str, str]]:
    """Split on the '## ' heading markers scrape.py leaves in the text."""
    out, heading, body = [], "", []
    for line in text.splitlines():
        if line.startswith("## "):
            if body:
                out.append((heading, "\n".join(body)))
            heading, body = line[3:].strip(), []
        else:
            body.append(line)
    if body:
        out.append((heading, "\n".join(body)))
    return out


def chunk(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Pack whole lines up to size; a line longer than size is cut with overlap."""
    if len(text) <= SECTION_MAX:
        return [text] if text.strip() else []
    pieces, cur = [], ""
    for line in text.splitlines():
        while len(line) > size:
            if cur:
                pieces.append(cur)
                cur = ""
            pieces.append(line[:size])
            line = line[size - overlap:]
        if cur and len(cur) + len(line) + 1 > size:
            pieces.append(cur)
            cur = cur[-overlap:].split("\n")[-1] if overlap else ""
        cur = f"{cur}\n{line}" if cur else line
    if cur.strip():
        pieces.append(cur)
    return pieces


def text_chunks(pages: list[dict]) -> tuple[list[str], list[dict]]:
    texts, metas, seen = [], [], set()
    for page in pages:
        title = page.get("title", "")
        position = 0
        for heading, body in sections(page["text"]):
            for piece in chunk(body):
                key = hashlib.md5(re.sub(r"\W+", " ", piece.lower()).encode()).hexdigest()
                if key in seen:          # page furniture repeated across pages
                    continue
                seen.add(key)
                label = f"{title} — {heading}" if heading and heading != title else title
                texts.append(f"{label}\n{piece}")
                metas.append({
                    "url": page["url"],
                    "site": page.get("site", ""),
                    "title": title,
                    "section": heading,
                    "position": position,
                    "kind": "text",
                    "page_type": page.get("page_type", ""),
                    "year": page.get("year", ""),
                })
                position += 1
    return texts, metas


def image_text(im: dict, description: str) -> str:
    parts = [f"Image on page: {im.get('page_title', '')} ({im.get('page', '')})"]
    if im.get("alt"):
        parts.append(f"Alt text: {im['alt']}")
    if im.get("caption"):
        parts.append(f"Caption: {im['caption']}")
    if description:
        parts.append(f"Description:\n{description}")
    return "\n".join(parts)[:IMAGE_TEXT_MAX]


def image_chunks(images: list[dict], descriptions: dict) -> tuple[list[str], list[dict]]:
    """Described images, plus undescribed ones whose alt or caption says something."""
    texts, metas = [], []
    for im in images:
        desc = (descriptions.get(im["src"]) or "").strip()
        meaningful = len(im.get("alt", "")) >= 15 or im.get("caption")
        if not desc and not meaningful:
            continue
        year = im.get("year") or (re.search(r"/uploads/(20\d\d)/", im["src"]) or [None, ""])[1]
        texts.append(image_text(im, desc))
        metas.append({
            "url": im.get("page", im["src"]),
            "image": im["src"],
            "title": im.get("page_title", ""),
            "section": "",
            "position": 0,
            "kind": "image",
            "described": bool(desc),
            "page_type": "image",
            "year": year,
        })
    return texts, metas


def build_index():
    pages = json.loads((DATA / "pages.json").read_text())
    images = json.loads((DATA / "images.json").read_text()) if (DATA / "images.json").exists() else []
    desc_path = DATA / "descriptions.json"
    descriptions = json.loads(desc_path.read_text()) if desc_path.exists() else {}

    t_texts, t_metas = text_chunks(pages)
    i_texts, i_metas = image_chunks(images, descriptions)
    texts, metas = t_texts + i_texts, t_metas + i_metas
    ids = [f"t{i}" for i in range(len(t_texts))] + [f"img{i}" for i in range(len(i_texts))]

    # Build beside the live index and swap only on success: a failed
    # embed (no network, 403) must never leave data/chroma empty.
    live, fresh, old = Path(STORE_PATH), DATA / "chroma.new", DATA / "chroma.old"
    for p in (fresh, old):
        if p.exists():
            shutil.rmtree(p)
    store = get_store(path=str(fresh), reset=True)
    add_to_store(store, texts, metas, ids=ids)
    if live.exists():
        live.rename(old)
    fresh.rename(live)
    shutil.rmtree(old, ignore_errors=True)
    described = sum(m["described"] for m in i_metas)
    print(f"indexed {len(t_texts)} text chunks, {len(i_texts)} image chunks "
          f"({described} described) -> {STORE_PATH}")


if __name__ == "__main__":
    build_index()
