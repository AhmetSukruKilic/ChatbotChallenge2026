"""Scraper. Workshop 1 block 4.

Reads each site's WordPress sitemap, extracts the main content of every
page as text with its headings kept, and collects image records in the
same pass. No gateway calls, so it runs anywhere with web access.

    python -m build.scrape            # writes data/pages.json, data/images.json
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, NavigableString

SITES = [
    "https://innowings.engg.hku.hk/",
    "https://innoacademy.engg.hku.hk/",
]

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

HEADERS = {"User-Agent": "Mozilla/5.0 (ChatbotChallenge2026 scraper)"}
WORKERS = 8

# Page chrome: removed before any text or image is read.
DROP = [
    "script", "style", "noscript", "template", "svg", "iframe", "form",
    "header", "footer", "nav", "aside",
    ".elementor-location-header", ".elementor-location-footer",
    ".elementor-nav-menu", ".elementor-menu-toggle", ".elementor-share-buttons",
    ".elementor-post-navigation", ".post-navigation", ".nav-links",
    "#comments", ".comments-area", ".sharedaddy", ".screen-reader-text",
    ".skip-link", "#wpadminbar",
]
ROOT_SELECTORS = ["main", "#content", ".site-content", "article", "body"]

IMG_SKIP = re.compile(r"logo|icon|favicon|avatar|emoji|spinner|loading|placeholder|banner-bg", re.I)
IMG_EXT = re.compile(r"\.(jpe?g|png|webp)(\?|$)", re.I)
SIZE_SUFFIX = re.compile(r"-\d+x\d+(?=\.\w+$)|-scaled(?=\.\w+$)")


def _get(url: str, session: requests.Session, tries: int = 3) -> str | None:
    for _ in range(tries):
        try:
            r = session.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r.text
            if r.status_code in (403, 404, 410):
                return None
        except requests.RequestException:
            pass
    return None


def sitemap_urls(site: str, session: requests.Session) -> list[tuple[str, str]]:
    """Return (url, page_type) for every post and page in the WP sitemap."""
    index = _get(urljoin(site, "wp-sitemap.xml"), session) or ""
    subs = re.findall(r"<loc>([^<]+)</loc>", index)
    out = []
    for sub in subs:
        m = re.search(r"wp-sitemap-posts-([a-z0-9_-]+?)-\d+\.xml", sub)
        if not m:                       # taxonomies and users: listing pages only
            continue
        xml = _get(sub, session) or ""
        out += [(u, m.group(1)) for u in re.findall(r"<loc>([^<]+)</loc>", xml)]
    return out


def crawl(start_url: str, session: requests.Session, max_pages: int = 500) -> list[tuple[str, str]]:
    """Fallback when there is no sitemap: breadth-first over internal links."""
    seen, queue, out = set(), [start_url], []
    domain = urlparse(start_url).netloc
    while queue and len(out) < max_pages:
        url = queue.pop(0).split("#")[0]
        if url in seen:
            continue
        seen.add(url)
        html = _get(url, session)
        if html is None:
            continue
        out.append((url, "page"))
        for a in BeautifulSoup(html, "html.parser").select("a[href]"):
            link = urljoin(url, a["href"]).split("#")[0]
            if urlparse(link).netloc == domain and link not in seen and not IMG_EXT.search(link):
                queue.append(link)
    return out


def _title(soup: BeautifulSoup) -> str:
    og = soup.select_one('meta[property="og:title"]')
    raw = (og.get("content") if og else None) or (soup.title.string if soup.title else "") or ""
    return re.sub(r"\s+[–|-]\s+Innovation (Wing|Academy)\s*$", "", raw).strip()


def _year(soup: BeautifulSoup, url: str) -> str:
    meta = soup.select_one('meta[property="article:published_time"]')
    if meta and meta.get("content", "")[:4].isdigit():
        return meta["content"][:4]
    m = re.search(r"(20[12]\d)", url)
    return m.group(1) if m else ""


def _content_root(soup: BeautifulSoup):
    for sel in ROOT_SELECTORS:
        el = soup.select_one(sel)
        if el and len(el.get_text(" ", strip=True)) > 50:
            return el
    return soup.body or soup


def _img_src(img, page_url: str) -> str:
    """Pick the largest srcset candidate up to ~1600px, else src or a lazy-load attribute."""
    srcset = img.get("srcset") or img.get("data-srcset") or ""
    best, best_w = None, 0
    for part in srcset.split(","):
        bits = part.strip().split()
        if len(bits) == 2 and bits[1].endswith("w") and bits[1][:-1].isdigit():
            w = int(bits[1][:-1])
            if best_w < w <= 1600 or (best_w > 1600 and w < best_w):
                best, best_w = bits[0], w
    src = best or img.get("data-src") or img.get("data-lazy-src") or img.get("src") or ""
    return urljoin(page_url, src.strip())


def _caption(img) -> str:
    fig = img.find_parent("figure")
    cap = fig.find("figcaption") if fig else None
    if cap is None:
        holder = img.find_parent(class_=re.compile(r"wp-caption|gallery-item|elementor-widget-image"))
        cap = holder.select_one(".wp-caption-text, .gallery-caption, .widget-image-caption") if holder else None
    return cap.get_text(" ", strip=True) if cap else ""


def _too_small(img) -> bool:
    for attr in ("width", "height"):
        v = str(img.get(attr, ""))
        if v.isdigit() and int(v) < 120:
            return True
    return False


def _text(root) -> str:
    """Text with headings marked '## ' and table rows joined by ' | '."""
    for tr in root.select("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        tr.replace_with(NavigableString("\n" + " | ".join(c for c in cells if c) + "\n"))
    for h in root.select("h1, h2, h3, h4"):
        label = h.get_text(" ", strip=True)
        h.replace_with(NavigableString(f"\n## {label}\n" if label else "\n"))
    for br in root.select("br"):
        br.replace_with("\n")
    raw = root.get_text("\n")
    lines = [re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in raw.splitlines()]
    out, prev = [], None
    for ln in lines:
        if ln and ln != prev:
            out.append(ln)
        prev = ln
    return "\n".join(out)


def extract(html: str, url: str, page_type: str) -> tuple[dict, list[dict]]:
    soup = BeautifulSoup(html, "html.parser")
    title, year = _title(soup), _year(soup, url)
    for sel in DROP:
        for el in soup.select(sel):
            el.decompose()
    root = _content_root(soup)

    images = []
    for img in root.select("img"):
        src = _img_src(img, url)
        if not src.startswith("http") or not IMG_EXT.search(src) or IMG_SKIP.search(src) or _too_small(img):
            continue
        images.append({
            "src": src,
            "alt": (img.get("alt") or "").strip(),
            "caption": _caption(img),
            "page": url,
            "page_title": title,
            "year": year,
        })

    page = {
        "url": url,
        "site": urlparse(url).netloc,
        "title": title,
        "page_type": page_type,
        "year": year,
        "text": _text(root),
    }
    return page, images


def scrape(sites: list[str] = SITES) -> tuple[list[dict], list[dict]]:
    session = requests.Session()
    targets = []
    for site in sites:
        found = sitemap_urls(site, session) or crawl(site, session)
        print(f"{site}: {len(found)} urls")
        targets += found
    targets = list(dict.fromkeys(targets))

    def work(item):
        url, page_type = item
        html = _get(url, session)
        return extract(html, url, page_type) if html else None

    pages, images, seen_img = [], [], set()
    with ThreadPoolExecutor(WORKERS) as pool:
        for i, res in enumerate(pool.map(work, targets), 1):
            if i % 100 == 0:
                print(f"  {i}/{len(targets)}")
            if res is None:
                continue
            page, imgs = res
            if len(page["text"]) >= 40:
                pages.append(page)
            for im in imgs:
                key = SIZE_SUFFIX.sub("", im["src"].split("?")[0])
                if key not in seen_img:
                    seen_img.add(key)
                    images.append(im)
    return pages, images


if __name__ == "__main__":
    pages, images = scrape()
    DATA.mkdir(exist_ok=True)
    (DATA / "pages.json").write_text(json.dumps(pages, indent=1, ensure_ascii=False))
    (DATA / "images.json").write_text(json.dumps(images, indent=1, ensure_ascii=False))
    print(f"{len(pages)} pages, {len(images)} images -> {DATA}")
