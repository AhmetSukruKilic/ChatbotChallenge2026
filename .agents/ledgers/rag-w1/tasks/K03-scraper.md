# K03 — Scraper
Seat: A (teammate) · Depends: K01 · Status: blocked (site URLs)
Read first: STATE.md, REFERENCE.md, then this.

## Goal
Owner's ask:

> i am answer and eval friend is index owner

Seat A owns the data. This task turns both Inno Wing sites into `data/pages.json` +
`data/images.json` per REFERENCE § Data contracts, with only real content text (ADR-K03).

## Non-negotiables
- Never `soup.get_text()` on the whole page — nav/footer boilerplate poisons every query.
- Relative `src`/`href` resolved with `urljoin` at scrape time.
- Same-domain only. Skip non-HTML (`.pdf .jpg .png .zip`), `mailto:`, `tel:`, fragments.
- Tests use fixtures, never the live sites.

## Context (anchors)
- `submission_repo/build/scrape.py:17` `SITES` — empty; fill from STATE.md once the owner pastes the URLs.
- `:22` `crawl` — BFS, link-following commented out (TODO).
- `:48` `extract` — `body = soup` (TODO), image collection already written.
- `:85-100` `__main__` — writes both JSON files.

## Steps
- [ ] Before code: fetch `<site>/sitemap.xml` and `<site>/robots.txt` for both sites; open two pages
      in a browser/`curl`, find the element wrapping content. Record selector per site in `## Notes`.
- [ ] Tests first, `tests/test_scrape.py` + fixtures `tests/fixtures/page_a.html`, `sitemap.xml`
      (invented content, nav + footer + `<main>` with two `<h2>` sections + relative `<img>`):
  - `extract` text contains the main body, not nav/footer words.
  - `sections` = two entries, headings match the `<h2>` text; text before first heading → heading `""`.
  - image `src` absolute; `caption` from `figcaption`.
  - `sitemap_urls(xml)` returns all `<loc>`; nested sitemap index followed once.
  - `crawl` (fake `requests.get`) follows internal links, ignores external, `.pdf`, `#frag`, stops at `max_pages`.
- [ ] `SITES = [{"url": ..., "selector": ...}, ...]`; `extract(html, url, selector)` falls back
      `main` → `article` → `body` if selector finds nothing, and logs which.
- [ ] `sections`: walk content element; each `h1–h3` starts a section.
- [ ] `sitemap_urls`, then `crawl` only when sitemap missing. Uncomment + finish link-following.
- [ ] Dedup pages by final URL (strip trailing `/`, query).
- [ ] `requests` headers: a `User-Agent`; `time.sleep(0.2)` between fetches.
- [ ] Run live `python -m build.scrape` (sites only, no gateway — agent may run if reachable).
      Print 5 random pages' first 200 chars; any nav text → fix selector.
- [ ] Commit `data/pages.json`, `data/images.json`.

## Definition of done
- Tests green. `data/pages.json` exists, every page has non-empty `text`, no page text starts with nav words.
- `## Notes` lists: page count per site, image count, selector per site, sitemap yes/no.

## Verification
`cd submission_repo && .venv/bin/python -m pytest -q tests/test_scrape.py && .venv/bin/python -c "import json;p=json.load(open('data/pages.json'));print(len(p),'pages',sum(len(x['images']) for x in p),'images');assert all(x['text'] and 'sections' in x for x in p)"`

## Notes
