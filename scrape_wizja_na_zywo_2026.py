#!/usr/bin/env python3
"""
Scraper collecting YouTube links for Krzysztof Jackowski's "Wizja na żywo"
entries published from 2026-01-01 onwards from archiwumwizji.pl.
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests

WARSAW_TZ = ZoneInfo("Europe/Warsaw")

BASE_CATEGORY_URL = (
    "https://archiwumwizji.pl/kategoria/archiwum-wizji/"
    "skroty-wizji/krzysztof-jackowski-skroty-wizji/"
)
START_DATE = "2026-01-01"
OUTPUT_CSV = Path(__file__).resolve().parent / "wizja_na_zywo_2026.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}

POLISH_MONTHS = {
    "stycznia": 1,
    "styczen": 1,
    "lutego": 2,
    "luty": 2,
    "marca": 3,
    "marzec": 3,
    "kwietnia": 4,
    "kwiecien": 4,
    "maja": 5,
    "maj": 5,
    "czerwca": 6,
    "czerwiec": 6,
    "lipca": 7,
    "lipiec": 7,
    "sierpnia": 8,
    "sierpien": 8,
    "wrzesnia": 9,
    "wrzesien": 9,
    "pazdziernika": 10,
    "pazdziernik": 10,
    "listopada": 11,
    "listopad": 11,
    "grudnia": 12,
    "grudzien": 12,
}

WIZJA_NA_ZYWO_RE = re.compile(r"\bwizja\s+na\s+zywo\b", re.IGNORECASE)

YOUTUBE_ID_PATTERNS = [
    re.compile(
        r"https?://(?:www\.|m\.)?youtube\.com/watch\?[^\"'\s<>]*?(?:&amp;|&|\?)?v=([A-Za-z0-9_-]{11})",
        re.IGNORECASE,
    ),
    re.compile(
        r"https?://(?:www\.)?youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_-]{11})",
        re.IGNORECASE,
    ),
    re.compile(
        r"https?://(?:www\.)?youtu\.be/([A-Za-z0-9_-]{11})",
        re.IGNORECASE,
    ),
    re.compile(
        r"https?://(?:www\.|m\.)?youtube\.com/(?:live|shorts)/([A-Za-z0-9_-]{11})",
        re.IGNORECASE,
    ),
]


def normalize_ascii(text: str) -> str:
    """Lowercase and strip Polish/Unicode diacritics."""
    text = text.replace("ł", "l").replace("Ł", "L")
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return stripped.lower()


def strip_tags(raw_html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_polish_date(date_text: str) -> str | None:
    """Parse Polish date like '20 listopada, 2026' -> '2026-11-20'."""
    norm = normalize_ascii(date_text)
    norm = re.sub(r"post published:", "", norm).strip()
    m = re.search(r"(\d{1,2})\s+([a-z]+),?\s+(\d{4})", norm)
    if not m:
        return None
    day = int(m.group(1))
    month_name = m.group(2)
    year = int(m.group(3))
    month = POLISH_MONTHS.get(month_name)
    if not month:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def fetch_url(session: requests.Session, url: str, retries: int = 3) -> str:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                resp.encoding = resp.apparent_encoding or "utf-8"
                return resp.text
            last_exc = RuntimeError(f"HTTP {resp.status_code} for {url}")
        except Exception as exc:
            last_exc = exc
        if attempt < retries:
            time.sleep(1.5 * attempt)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts: {last_exc}")


def parse_category_page(page_html: str) -> tuple[list[dict[str, Any]], str | None]:
    """Extract post entries and next-page URL from a category page."""
    entries: list[dict[str, Any]] = []
    for m in re.finditer(
        r'(<article\s+id="post-(\d+)"\s+class="[^"]*blog-entry[^"]*"[^>]*>.*?</article>)',
        page_html,
        re.S,
    ):
        block = m.group(1)
        post_id = m.group(2)

        h2_match = re.search(
            r'<h2[^>]*class="[^"]*entry-title[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            block,
            re.S,
        )
        if not h2_match:
            continue
        url = html.unescape(h2_match.group(1).strip())
        title = strip_tags(h2_match.group(2))

        date_match = re.search(
            r'<li[^>]*class="[^"]*meta-date[^"]*"[^>]*>(.*?)</li>', block, re.S
        )
        raw_date = strip_tags(date_match.group(1)) if date_match else ""
        list_date = parse_polish_date(raw_date)

        entries.append(
            {
                "post_id": post_id,
                "url": url,
                "title": title,
                "list_date_raw": raw_date,
                "list_date": list_date,
            }
        )

    next_match = re.search(
        r'<a[^>]*class="next page-numbers"[^>]*href="([^"]+)"', page_html, re.S
    )
    next_url = html.unescape(next_match.group(1)) if next_match else None
    return entries, next_url


def extract_youtube_ids(html_fragment: str) -> list[str]:
    """Extract unique YouTube video IDs in order of appearance."""
    unescaped = html.unescape(html_fragment)
    matches_with_pos: list[tuple[int, str]] = []
    for pat in YOUTUBE_ID_PATTERNS:
        for m in pat.finditer(unescaped):
            matches_with_pos.append((m.start(), m.group(1)))
    matches_with_pos.sort(key=lambda item: item[0])

    seen: set[str] = set()
    ordered_ids: list[str] = []
    for _, vid in matches_with_pos:
        if vid not in seen:
            seen.add(vid)
            ordered_ids.append(vid)
    return ordered_ids


def extract_youtube_iframe_titles(html_fragment: str) -> list[str]:
    """Extract title attributes from YouTube iframe embeds (any attribute order)."""
    titles: list[str] = []
    for tag in re.findall(r"<iframe\b[^>]*>", html_fragment, re.I):
        if not re.search(r"youtube(?:-nocookie)?\.com|youtu\.be", tag, re.I):
            continue
        t_m = re.search(r'\btitle="([^"]*)"', tag, re.I)
        if t_m:
            titles.append(html.unescape(t_m.group(1)).strip())
    return titles


def parse_post_page(post_html: str) -> dict[str, Any]:
    """Extract publication date, YouTube video IDs, and YouTube iframe titles from a post page."""
    # Exact publication timestamp from Yoast/OpenGraph or JSON-LD.
    # Note: archiwumwizji.pl's WordPress stores site-local dates with '+00:00' offset,
    # so the ISO date prefix (UTC date) matches the visible site date (<li class="meta-date">).
    pub_iso = None
    meta_match = re.search(
        r'<meta\s+property="article:published_time"\s+content="([^"]+)"',
        post_html,
        re.I,
    )
    if meta_match:
        pub_iso = meta_match.group(1).strip()
    else:
        ld_match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', post_html)
        if ld_match:
            pub_iso = ld_match.group(1).strip()

    pub_date_meta = None
    if pub_iso:
        dt = datetime.fromisoformat(pub_iso.replace("Z", "+00:00"))
        pub_date_meta = dt.astimezone(timezone.utc).strftime("%Y-%m-%d")

    vis_match = re.search(
        r'<li[^>]*class="[^"]*meta-date[^"]*"[^>]*>(.*?)</li>', post_html, re.S
    )
    vis_date_raw = strip_tags(vis_match.group(1)) if vis_match else ""
    vis_date = parse_polish_date(vis_date_raw)

    # Isolate main post <article id="post-..."> to exclude sidebar/footer/comments/related posts
    article_match = re.search(
        r'<article\s+id="post-\d+"[^>]*>(.*?)</article>', post_html, re.S
    )
    article_html = article_match.group(1) if article_match else post_html

    content_start = re.search(
        r'<div[^>]*class="[^"]*entry-content[^"]*"[^>]*>', article_html, re.S
    )
    if content_start:
        content_html = article_html[content_start.start() :]
        for end_marker in [
            r'<section[^>]*id="related-posts"',
            r'<section[^>]*id="comments"',
            r'<div[^>]*id="comments"',
            r'<nav[^>]*class="[^"]*post-navigation',
        ]:
            end_m = re.search(end_marker, content_html, re.S | re.I)
            if end_m:
                content_html = content_html[: end_m.start()]
    else:
        content_html = article_html

    yt_ids = extract_youtube_ids(content_html)
    iframe_titles = extract_youtube_iframe_titles(content_html)
    if not yt_ids and content_html != article_html:
        yt_ids = extract_youtube_ids(article_html)
        iframe_titles = extract_youtube_iframe_titles(article_html)

    return {
        "pub_iso": pub_iso,
        "pub_date_meta": pub_date_meta,
        "vis_date": vis_date,
        "vis_date_raw": vis_date_raw,
        "youtube_ids": yt_ids,
        "iframe_titles": iframe_titles,
    }


def is_wizja_na_zywo(text: str) -> bool:
    return bool(WIZJA_NA_ZYWO_RE.search(normalize_ascii(text)))


def main() -> int:
    session = requests.Session()

    all_entries: list[dict[str, Any]] = []
    seen_post_urls: set[str] = set()
    page_stats: list[dict[str, Any]] = []

    current_url: str | None = BASE_CATEGORY_URL
    page_num = 0

    while current_url:
        page_num += 1
        page_html = fetch_url(session, current_url)
        entries, next_url = parse_category_page(page_html)
        if not entries:
            raise RuntimeError(
                f"No blog-entry articles parsed on page {page_num}: {current_url}"
            )

        dates_on_page = [e["list_date"] for e in entries if e["list_date"]]
        min_d = min(dates_on_page) if dates_on_page else None
        max_d = max(dates_on_page) if dates_on_page else None
        page_stats.append(
            {
                "page": page_num,
                "url": current_url,
                "count": len(entries),
                "min_date": min_d,
                "max_date": max_d,
                "has_next": bool(next_url),
            }
        )
        print(
            f"[Page {page_num}] {len(entries)} entries | dates: {min_d} .. {max_d} | next={bool(next_url)}"
        )

        for e in entries:
            e["page"] = page_num
            if e["url"] not in seen_post_urls:
                seen_post_urls.add(e["url"])
                all_entries.append(e)

        # Stop once an entire page consists solely of posts older than START_DATE
        if max_d and max_d < START_DATE:
            print(
                f"Stopping pagination after page {page_num}: all entries older than {START_DATE} (max={max_d})."
            )
            break

        current_url = next_url

    # Inspect all 2026+ entries (so we catch both post-title and YouTube-embed-title matches)
    entries_2026_or_unknown = [
        e for e in all_entries if not e["list_date"] or e["list_date"] >= START_DATE
    ]
    print(f"\nTotal category entries visited across {page_num} pages: {len(all_entries)}")
    print(f"Entries >= {START_DATE} to inspect: {len(entries_2026_or_unknown)}")

    def fetch_and_parse(entry: dict[str, Any]) -> dict[str, Any]:
        s = requests.Session()
        post_html = fetch_url(s, entry["url"])
        parsed = parse_post_page(post_html)
        return {**entry, **parsed}

    detailed_results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(fetch_and_parse, e): e for e in entries_2026_or_unknown
        }
        for fut in as_completed(futures):
            detailed_results.append(fut.result())

    # Classify Wizja na żywo posts (match in post title OR embedded YouTube iframe title)
    matched_posts: list[dict[str, Any]] = []
    excluded_posts: list[dict[str, Any]] = []
    date_mismatches: list[dict[str, Any]] = []
    missing_youtube: list[dict[str, Any]] = []
    multi_youtube: list[dict[str, Any]] = []

    for r in detailed_results:
        pub_date = r["pub_date_meta"] or r["vis_date"] or r["list_date"]
        if not pub_date:
            raise RuntimeError(f"Could not determine publication date for {r['url']}")
        r["pub_date"] = pub_date

        dates_set = {
            d for d in [r["pub_date_meta"], r["vis_date"], r["list_date"]] if d
        }
        if len(dates_set) > 1:
            date_mismatches.append(
                {
                    "url": r["url"],
                    "pub_date_meta": r["pub_date_meta"],
                    "vis_date": r["vis_date"],
                    "list_date": r["list_date"],
                }
            )

        if pub_date < START_DATE:
            excluded_posts.append({**r, "reason": "before_start_date"})
            continue

        title_match = is_wizja_na_zywo(r["title"])
        iframe_match = any(is_wizja_na_zywo(t) for t in r["iframe_titles"])
        if title_match or iframe_match:
            r["match_via"] = (
                "title+iframe"
                if (title_match and iframe_match)
                else ("title" if title_match else "iframe_title")
            )
            matched_posts.append(r)
        else:
            excluded_posts.append({**r, "reason": "not_wizja_na_zywo"})

    matched_posts.sort(key=lambda r: (r["pub_date"], r["url"]), reverse=True)

    # Deduplicate by youtube_url, keeping the earliest publication date if the site
    # accidentally re-embedded an earlier video on a newer post.
    url_occurrences: dict[str, list[dict[str, Any]]] = {}
    for r in matched_posts:
        yt_ids = r["youtube_ids"]
        if not yt_ids:
            missing_youtube.append(
                {"date": r["pub_date"], "title": r["title"], "url": r["url"]}
            )
            continue
        if len(yt_ids) > 1:
            multi_youtube.append(
                {
                    "date": r["pub_date"],
                    "title": r["title"],
                    "url": r["url"],
                    "youtube_ids": yt_ids,
                }
            )
        for vid in yt_ids:
            yt_url = f"https://www.youtube.com/watch?v={vid}"
            url_occurrences.setdefault(yt_url, []).append(
                {
                    "date": r["pub_date"],
                    "title": r["title"],
                    "post_url": r["url"],
                    "match_via": r["match_via"],
                }
            )

    duplicate_yt_urls: dict[str, list[dict[str, Any]]] = {
        u: occs for u, occs in url_occurrences.items() if len(occs) > 1
    }

    def resolve_duplicate_date(yt_url: str, occs: list[dict[str, Any]]) -> str:
        """Pick the post date matching the actual YouTube upload date if available."""
        candidate_dates = sorted({o["date"] for o in occs})
        if len(candidate_dates) == 1:
            return candidate_dates[0]
        try:
            yt_html = fetch_url(session, yt_url, retries=2)
            pub_matches = re.findall(
                r'"(?:publishDate|uploadDate)"\s*:\s*"([^"]+)"', yt_html
            )
            for iso_str in pub_matches:
                try:
                    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
                    yt_warsaw_date = dt.astimezone(WARSAW_TZ).strftime("%Y-%m-%d")
                    if yt_warsaw_date in candidate_dates:
                        return yt_warsaw_date
                except ValueError:
                    continue
        except Exception:
            pass
        # Fallback: prefer title-matched occurrence, then earliest date
        title_occs = [o for o in occs if "title" in o["match_via"].split("+")]
        pool = title_occs if title_occs else occs
        return min(o["date"] for o in pool)

    final_rows: list[tuple[str, str]] = []
    for yt_url, occs in url_occurrences.items():
        if len(occs) == 1:
            chosen_date = occs[0]["date"]
        else:
            chosen_date = resolve_duplicate_date(yt_url, occs)
        final_rows.append((chosen_date, yt_url))

    # Sort descending by publication date, ascending by URL as deterministic tie-breaker
    final_rows.sort(key=lambda row: row[1])
    final_rows.sort(key=lambda row: row[0], reverse=True)

    # Validate output before writing
    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    yt_re = re.compile(r"^https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}$")
    seen_urls: set[str] = set()
    for d, u in final_rows:
        if not date_re.match(d) or d < START_DATE:
            raise RuntimeError(f"Invalid publication date in output: {d} ({u})")
        if not yt_re.match(u):
            raise RuntimeError(f"Invalid YouTube URL in output: {u} ({d})")
        if u in seen_urls:
            raise RuntimeError(f"Duplicate YouTube URL in output: {u}")
        seen_urls.add(u)

    # Write CSV
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["data_publikacji", "youtube_url"])
        writer.writerows(final_rows)

    print("\n=== SUMMARY ===")
    print(f"CSV written to: {OUTPUT_CSV}")
    print(f"Matched 'Wizja na żywo' posts (>= {START_DATE}): {len(matched_posts)}")
    print(
        f"  - via post title: {sum(1 for r in matched_posts if 'title' in r['match_via'].split('+'))}"
    )
    print(
        f"  - via YouTube iframe title only: {sum(1 for r in matched_posts if r['match_via'] == 'iframe_title')}"
    )
    print(f"Excluded category posts: {len(excluded_posts)}")
    for ex in excluded_posts:
        print(
            f"  EXCLUDED ({ex['reason']}): [{ex['pub_date']}] {ex['title']} | iframes={ex['iframe_titles']} | {ex['url']}"
        )
    print(f"Unique YouTube videos written to CSV: {len(final_rows)}")
    if final_rows:
        print(f"Date range: {final_rows[-1][0]} .. {final_rows[0][0]}")
    print(f"Date mismatches (meta vs visible vs list): {len(date_mismatches)}")
    print(f"Matching posts missing YouTube link: {len(missing_youtube)}")
    for my in missing_youtube:
        print("  MISSING YT:", my)
    print(f"Matching posts with multiple YouTube links: {len(multi_youtube)}")
    print(f"Duplicate YouTube URLs across posts (deduplicated): {len(duplicate_yt_urls)}")
    for u, occs in duplicate_yt_urls.items():
        print(f"  DUP YT {u}: {[(o['date'], o['post_url']) for o in occs]}")

    report = {
        "page_stats": page_stats,
        "total_category_entries": len(all_entries),
        "matched_posts_count": len(matched_posts),
        "excluded_posts": [
            {
                "date": ex["pub_date"],
                "title": ex["title"],
                "url": ex["url"],
                "iframe_titles": ex["iframe_titles"],
                "reason": ex["reason"],
            }
            for ex in excluded_posts
        ],
        "date_mismatches": date_mismatches,
        "missing_youtube": missing_youtube,
        "multi_youtube": multi_youtube,
        "duplicate_yt_urls": duplicate_yt_urls,
        "final_row_count": len(final_rows),
        "date_range": [final_rows[-1][0], final_rows[0][0]] if final_rows else None,
    }
    Path("/tmp/wizja_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
