#!/usr/bin/env python3
"""Fetch Ultimate Guitar tabs for songs in the catalog and store JSON payloads."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent

def resolve_data_root(base_dir: Path) -> Path:
    data_root_env = os.getenv("BCH_DATA_DIR") or os.getenv("DATA_DIR")
    if not data_root_env:
        return base_dir
    data_root = Path(data_root_env).expanduser()
    if not data_root.is_absolute():
        data_root = base_dir / data_root
    return data_root.resolve()

DATA_ROOT = resolve_data_root(BASE_DIR)
SONGLIST_FILE = (
    DATA_ROOT
    / "songlist"
    / "Buckingham Conspiracy 3.0  SONG LIST"
    / "Buckingham Conspiracy 3.0  SONG LIST.md"
)
TABS_DIR = DATA_ROOT / "song_data" / "tabs"
DEFAULT_UG_API_DIR = BASE_DIR.parent.parent / "Ultimate-Guitar-Tabs" / "ultimate-api"
UG_SEARCH_URL = "https://www.ultimate-guitar.com/search.php"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0 Safari/537.36"
)
MARKER_PATTERN = re.compile(r"\^.*?\^")
PREFERRED_TYPES = ("Official", "Chords", "Tabs", "Bass Tabs", "Ukulele Chords")


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def display_path(path: Path) -> str:
    for root in (DATA_ROOT, BASE_DIR):
        try:
            return str(path.relative_to(root))
        except ValueError:
            continue
    return str(path)


def parse_song_list() -> Dict[str, Dict[str, str]]:
    songs: Dict[str, Dict[str, str]] = {}
    with SONGLIST_FILE.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "(" not in line:
                continue
            clean_line = MARKER_PATTERN.sub("", line)
            match = re.search(r"^(.+?)\s*\((\d+)\)", clean_line)
            if not match:
                continue
            title_artist = match.group(1).strip()
            title = title_artist
            artist = ""
            if " - " in title_artist:
                title, artist = [part.strip() for part in title_artist.split(" - ", 1)]
            songs[title] = {"artist": artist, "raw": line}
    return songs


def determine_targets(options: argparse.Namespace, songs: Dict[str, Dict[str, str]]) -> List[str]:
    if options.song:
        if options.song not in songs:
            raise SystemExit(f"Song '{options.song}' was not found in the markdown list.")
        return [options.song]
    if not options.all_missing:
        raise SystemExit("Use --song or --all-missing to select which songs to fetch.")
    targets: List[str] = []
    for title in sorted(songs.keys()):
        destination = TABS_DIR / f"{title}.json"
        if destination.exists() and not options.overwrite:
            continue
        targets.append(title)
        if options.limit and len(targets) >= options.limit:
            break
    return targets


def load_tab_parser(ug_api_dir: Path):
    ug_api_dir = ug_api_dir.expanduser().resolve()
    server_dir = ug_api_dir / "server"
    if not server_dir.exists():
        raise SystemExit(
            f"Ultimate-Guitar API directory '{ug_api_dir}' does not look valid."
        )
    if str(ug_api_dir) not in sys.path:
        sys.path.insert(0, str(ug_api_dir))
    try:
        from server.tab_parser import dict_from_ultimate_tab  # type: ignore
    except ImportError as exc:  # pragma: no cover - runtime safety
        raise SystemExit(
            "Could not import server.tab_parser from the Ultimate-Guitar API repo."
        ) from exc
    return dict_from_ultimate_tab


def fetch_search_results(query: str) -> Sequence[Dict]:
    params = {"search_type": "title", "value": query}
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(UG_SEARCH_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        print(f"  ✗ Ultimate Guitar search returned {status} for query '{query}'")
        return []
    except requests.RequestException as exc:
        print(f"  ✗ Network error talking to Ultimate Guitar: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    store_element = soup.find("div", {"class": "js-store"})
    if not store_element:
        return []
    try:
        payload = json.loads(store_element["data-content"])
    except (KeyError, json.JSONDecodeError):
        return []
    results: Sequence[Dict] = (
        payload
        .get("store", {})
        .get("page", {})
        .get("data", {})
        .get("results", [])
    )
    return results


def score_entry(entry: Dict, title_norm: str, artist_norm: str, prefer_type: str) -> float:
    try:
        score = float(entry.get("rating", 0.0) or 0.0)
    except (TypeError, ValueError):
        score = 0.0
    try:
        votes_value = float(entry.get("votes", 0) or 0)
    except (TypeError, ValueError):
        votes_value = 0.0
    score += min(votes_value / 100.0, 5.0)
    entry_title = normalize(entry.get("song_name", ""))
    entry_artist = normalize(entry.get("artist_name", ""))
    if title_norm and title_norm == entry_title:
        score += 5
    elif title_norm and title_norm in entry_title:
        score += 2
    if artist_norm and artist_norm == entry_artist:
        score += 4
    elif artist_norm and artist_norm in entry_artist:
        score += 1.5
    entry_type = (entry.get("type") or "").lower()
    if prefer_type and prefer_type in entry_type:
        score += 2
    elif any(t.lower() in entry_type for t in PREFERRED_TYPES):
        score += 1
    return score


def choose_tab_url(
    title: str,
    artist: str,
    prefer_type: str,
    manual_url: Optional[str] = None,
) -> Optional[str]:
    if manual_url:
        return manual_url
    query = f"{title} {artist}".strip()
    results = fetch_search_results(query or title)
    if not results:
        return None
    title_norm = normalize(title)
    artist_norm = normalize(artist)
    candidates: List[tuple[float, str]] = []
    for entry in results:
        url = entry.get("tab_url", "")
        if not url.startswith("https://tabs.ultimate-guitar.com/tab/"):
            continue
        if entry.get("tab_access_type") != "public":
            continue
        score = score_entry(entry, title_norm, artist_norm, prefer_type)
        candidates.append((score, url))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def save_tab_payload(title: str, payload: Dict) -> Path:
    TABS_DIR.mkdir(parents=True, exist_ok=True)
    destination = TABS_DIR / f"{title}.json"
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def fetch_tab_for_song(
    title: str,
    artist: str,
    parser_func,
    prefer_type: str,
    manual_url: Optional[str] = None,
) -> Optional[Path]:
    tab_url = choose_tab_url(title, artist, prefer_type, manual_url=manual_url)
    if not tab_url:
        print(f"  ✗ No Ultimate Guitar tab URL found for '{title}'")
        return None
    print(f"  → Using tab URL: {tab_url}")
    try:
        payload = parser_func(tab_url)
    except Exception as exc:  # pragma: no cover - network heavy
        print(f"  ✗ Failed to parse tab page: {exc}")
        return None
    destination = save_tab_payload(title, payload)
    print(f"  ✓ Saved JSON to {display_path(destination)}")
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Ultimate Guitar tabs for Buckingham Conspiracy songs."
    )
    parser.add_argument("--song", help="Exact song title from the markdown list.")
    parser.add_argument(
        "--all-missing",
        action="store_true",
        help="Process every song that does not yet have a JSON tab payload.",
    )
    parser.add_argument("--limit", type=int, help="Limit the number of songs fetched.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate JSON files even if they already exist.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between requests (default: 1).",
    )
    parser.add_argument(
        "--api-path",
        type=Path,
        default=DEFAULT_UG_API_DIR,
        help="Path to the Ultimate-Guitar-Tabs/ultimate-api directory.",
    )
    parser.add_argument(
        "--prefer",
        choices=["chords", "tabs", "any"],
        default="chords",
        help="Tab type preference when multiple matches exist (default: chords).",
    )
    parser.add_argument(
        "--manual-url",
        help="Provide a direct Ultimate Guitar tab URL instead of searching.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    options = parser.parse_args()
    songs = parse_song_list()
    targets = determine_targets(options, songs)
    if not targets:
        print("No songs matched the requested criteria.")
        return 0

    parser_func = load_tab_parser(options.api_path)
    prefer_fragment = "" if options.prefer == "any" else options.prefer

    successes = 0
    for index, title in enumerate(targets, start=1):
        artist = songs[title]["artist"]
        print(
            f"[{index}/{len(targets)}] Fetching '{title}' "
            f"({artist or 'Unknown artist'})..."
        )
        destination = fetch_tab_for_song(
            title,
            artist,
            parser_func,
            prefer_fragment,
            manual_url=options.manual_url,
        )
        if destination:
            successes += 1
        if index < len(targets) and options.delay > 0:
            time.sleep(options.delay)

    print(f"Done. {successes} of {len(targets)} songs populated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
