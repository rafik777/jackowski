#!/usr/bin/env python3
"""
Download Polish YouTube transcripts for all videos in wizja_na_zywo_2026.csv
and store them in SQLite (jackowski.db) + JSON export (transkrypcje.json).
"""

from __future__ import annotations

import csv
import html
import json
import re
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = BASE_DIR / "wizja_na_zywo_2026.csv"
DB_PATH = BASE_DIR / "jackowski.db"
TRANSCRIPTS_JSON = BASE_DIR / "transkrypcje.json"

INNERTUBE_URL = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
ANDROID_HEADERS = {
    "User-Agent": "com.google.android.youtube/20.10.38 (Linux; U; Android 14)",
    "Content-Type": "application/json",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}

VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|embed/|live/)([A-Za-z0-9_-]{11})")


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS filmy (
            video_id TEXT PRIMARY KEY,
            data_publikacji TEXT NOT NULL,
            youtube_url TEXT NOT NULL,
            tytul TEXT,
            dlugosc_sek INTEGER,
            status_transkrypcji TEXT NOT NULL,
            jezyk TEXT,
            rodzaj_napisow TEXT,
            liczba_znakow INTEGER DEFAULT 0,
            liczba_segmentow INTEGER DEFAULT 0,
            transkrypcja_tekst TEXT,
            transkrypcja_segmenty_json TEXT,
            blad TEXT,
            pobrano_o TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tezy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL REFERENCES filmy(video_id),
            data_wypowiedzenia TEXT NOT NULL,
            teza TEXT NOT NULL,
            kategoria TEXT,
            horyzont_czasowy TEXT,
            timestamp_sek INTEGER,
            cytat_zrodlowy TEXT,
            youtube_link_z_czasem TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_filmy_data ON filmy(data_publikacji DESC);
        CREATE INDEX IF NOT EXISTS idx_tezy_data ON tezy(data_wypowiedzenia DESC);
        CREATE INDEX IF NOT EXISTS idx_tezy_video ON tezy(video_id);
        """
    )
    conn.commit()


def extract_video_id(url: str) -> str:
    m = VIDEO_ID_RE.search(url)
    if not m:
        raise ValueError(f"Cannot extract video ID from URL: {url}")
    return m.group(1)


def parse_timedtext_xml(xml_text: str) -> tuple[list[dict[str, Any]], str]:
    """Parse YouTube timedtext XML (format 3 or legacy <text>) into segments and clean full text."""
    root = ET.fromstring(xml_text)
    segments: list[dict[str, Any]] = []

    # Format 3: <body><p t="ms" d="ms"><s>word</s>...</p></body>
    p_nodes = root.findall(".//body/p")
    if p_nodes:
        for p in p_nodes:
            t_ms = int(p.attrib.get("t", "0"))
            d_ms = int(p.attrib.get("d", "0"))
            s_nodes = p.findall("s")
            if s_nodes:
                raw_text = "".join(s.text or "" for s in s_nodes)
            else:
                raw_text = "".join(p.itertext())
            clean = re.sub(r"\s+", " ", html.unescape(raw_text)).strip()
            if not clean:
                continue
            segments.append(
                {
                    "start": round(t_ms / 1000.0, 2),
                    "duration": round(d_ms / 1000.0, 2),
                    "text": clean,
                }
            )
    else:
        # Legacy format: <transcript><text start="sec" dur="sec">...</text></transcript>
        for node in root.findall(".//text"):
            start = float(node.attrib.get("start", "0"))
            dur = float(node.attrib.get("dur", "0"))
            raw_text = "".join(node.itertext())
            clean = re.sub(r"\s+", " ", html.unescape(raw_text)).strip()
            if not clean:
                continue
            segments.append(
                {
                    "start": round(start, 2),
                    "duration": round(dur, 2),
                    "text": clean,
                }
            )

    full_text = " ".join(seg["text"] for seg in segments)
    full_text = re.sub(r"\s+", " ", full_text).strip()
    return segments, full_text


def choose_track(tracks: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not tracks:
        return None
    # 1. Polish manual captions
    for t in tracks:
        if t.get("languageCode", "").startswith("pl") and t.get("kind") != "asr":
            return t
    # 2. Polish auto-generated captions (asr)
    for t in tracks:
        if t.get("languageCode", "").startswith("pl"):
            return t
    # 3. Any available track
    return tracks[0]


def fetch_video_transcript(data_publikacji: str, youtube_url: str) -> dict[str, Any]:
    video_id = extract_video_id(youtube_url)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    session = requests.Session()

    payload = {
        "context": {
            "client": {
                "clientName": "ANDROID",
                "clientVersion": "20.10.38",
                "hl": "pl",
                "gl": "PL",
            }
        },
        "videoId": video_id,
    }

    last_err: str | None = None
    for attempt in range(1, 4):
        try:
            resp = session.post(
                INNERTUBE_URL, json=payload, headers=ANDROID_HEADERS, timeout=25
            )
            if resp.status_code != 200:
                last_err = f"Innertube HTTP {resp.status_code}"
                time.sleep(1.5 * attempt)
                continue

            data = resp.json()
            vd = data.get("videoDetails") or {}
            title = vd.get("title")
            length_sec = int(vd["lengthSeconds"]) if vd.get("lengthSeconds") else None

            playability = (data.get("playabilityStatus") or {}).get("status")
            tracks = (
                data.get("captions", {})
                .get("playerCaptionsTracklistRenderer", {})
                .get("captionTracks", [])
            )
            track = choose_track(tracks)
            if not track:
                return {
                    "video_id": video_id,
                    "data_publikacji": data_publikacji,
                    "youtube_url": youtube_url,
                    "tytul": title,
                    "dlugosc_sek": length_sec,
                    "status_transkrypcji": "brak",
                    "jezyk": None,
                    "rodzaj_napisow": None,
                    "liczba_znakow": 0,
                    "liczba_segmentow": 0,
                    "transkrypcja_tekst": None,
                    "transkrypcja_segmenty_json": None,
                    "blad": f"Brak ścieżek napisów (playability={playability})",
                    "pobrano_o": now_iso,
                }

            t_resp = session.get(track["baseUrl"], timeout=25)
            if t_resp.status_code != 200 or not t_resp.text.strip():
                last_err = f"Timedtext HTTP {t_resp.status_code}, len={len(t_resp.text)}"
                time.sleep(1.5 * attempt)
                continue

            segments, full_text = parse_timedtext_xml(t_resp.text)
            if not full_text:
                last_err = "Pusta transkrypcja po parsowaniu XML"
                time.sleep(1.5 * attempt)
                continue

            return {
                "video_id": video_id,
                "data_publikacji": data_publikacji,
                "youtube_url": youtube_url,
                "tytul": title,
                "dlugosc_sek": length_sec,
                "status_transkrypcji": "ok",
                "jezyk": track.get("languageCode"),
                "rodzaj_napisow": "asr" if track.get("kind") == "asr" else "manual",
                "liczba_znakow": len(full_text),
                "liczba_segmentow": len(segments),
                "transkrypcja_tekst": full_text,
                "transkrypcja_segmenty_json": json.dumps(segments, ensure_ascii=False),
                "blad": None,
                "pobrano_o": now_iso,
            }
        except Exception as exc:
            last_err = str(exc)
            if attempt < 3:
                time.sleep(1.5 * attempt)

    return {
        "video_id": video_id,
        "data_publikacji": data_publikacji,
        "youtube_url": youtube_url,
        "tytul": None,
        "dlugosc_sek": None,
        "status_transkrypcji": "blad",
        "jezyk": None,
        "rodzaj_napisow": None,
        "liczba_znakow": 0,
        "liczba_segmentow": 0,
        "transkrypcja_tekst": None,
        "transkrypcja_segmenty_json": None,
        "blad": last_err,
        "pobrano_o": now_iso,
    }


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"ERROR: Missing input CSV: {INPUT_CSV}", file=sys.stderr)
        return 1

    with INPUT_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # Check already fetched OK videos for resumability
    existing_ok = {
        row[0]
        for row in conn.execute(
            "SELECT video_id FROM filmy WHERE status_transkrypcji = 'ok'"
        ).fetchall()
    }

    to_fetch = []
    for r in rows:
        vid = extract_video_id(r["youtube_url"])
        if vid not in existing_ok:
            to_fetch.append((r["data_publikacji"], r["youtube_url"]))

    print(
        f"Total videos in CSV: {len(rows)} | Already OK in DB: {len(existing_ok)} | To fetch: {len(to_fetch)}"
    )

    fetched_results: list[dict[str, Any]] = []
    if to_fetch:
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(fetch_video_transcript, d, u): (d, u)
                for d, u in to_fetch
            }
            done_count = 0
            for fut in as_completed(futures):
                res = fut.result()
                fetched_results.append(res)
                done_count += 1
                conn.execute(
                    """
                    INSERT INTO filmy (
                        video_id, data_publikacji, youtube_url, tytul, dlugosc_sek,
                        status_transkrypcji, jezyk, rodzaj_napisow, liczba_znakow,
                        liczba_segmentow, transkrypcja_tekst, transkrypcja_segmenty_json,
                        blad, pobrano_o
                    ) VALUES (
                        :video_id, :data_publikacji, :youtube_url, :tytul, :dlugosc_sek,
                        :status_transkrypcji, :jezyk, :rodzaj_napisow, :liczba_znakow,
                        :liczba_segmentow, :transkrypcja_tekst, :transkrypcja_segmenty_json,
                        :blad, :pobrano_o
                    )
                    ON CONFLICT(video_id) DO UPDATE SET
                        data_publikacji = excluded.data_publikacji,
                        youtube_url = excluded.youtube_url,
                        tytul = excluded.tytul,
                        dlugosc_sek = excluded.dlugosc_sek,
                        status_transkrypcji = excluded.status_transkrypcji,
                        jezyk = excluded.jezyk,
                        rodzaj_napisow = excluded.rodzaj_napisow,
                        liczba_znakow = excluded.liczba_znakow,
                        liczba_segmentow = excluded.liczba_segmentow,
                        transkrypcja_tekst = excluded.transkrypcja_tekst,
                        transkrypcja_segmenty_json = excluded.transkrypcja_segmenty_json,
                        blad = excluded.blad,
                        pobrano_o = excluded.pobrano_o
                    """,
                    res,
                )
                conn.commit()
                print(
                    f"[{done_count}/{len(to_fetch)}] {res['data_publikacji']} {res['video_id']} "
                    f"status={res['status_transkrypcji']} chars={res['liczba_znakow']}"
                    + (f" err={res['blad']}" if res["blad"] else "")
                )

    # Export transkrypcje.json ordered by date descending
    conn.row_factory = sqlite3.Row
    all_films = [
        dict(row)
        for row in conn.execute(
            """
            SELECT video_id, data_publikacji, youtube_url, tytul, dlugosc_sek,
                   status_transkrypcji, jezyk, rodzaj_napisow, liczba_znakow,
                   liczba_segmentow, transkrypcja_tekst, blad, pobrano_o
            FROM filmy
            ORDER BY data_publikacji DESC, video_id ASC
            """
        ).fetchall()
    ]
    TRANSCRIPTS_JSON.write_text(
        json.dumps(all_films, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    ok_count = sum(1 for x in all_films if x["status_transkrypcji"] == "ok")
    brak_count = sum(1 for x in all_films if x["status_transkrypcji"] == "brak")
    blad_count = sum(1 for x in all_films if x["status_transkrypcji"] == "blad")
    total_chars = sum(x["liczba_znakow"] or 0 for x in all_films)

    print("\n=== TRANSCRIPTS SUMMARY ===")
    print(f"DB: {DB_PATH}")
    print(f"JSON: {TRANSCRIPTS_JSON}")
    print(f"Total: {len(all_films)} | OK: {ok_count} | Brak: {brak_count} | Blad: {blad_count}")
    print(f"Total transcript characters: {total_chars:,}")
    if brak_count or blad_count:
        for x in all_films:
            if x["status_transkrypcji"] != "ok":
                print(f"  NON-OK: {x['data_publikacji']} {x['video_id']} ({x['status_transkrypcji']}): {x['blad']}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
