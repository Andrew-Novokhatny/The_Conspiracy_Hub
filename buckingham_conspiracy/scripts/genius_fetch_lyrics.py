#!/usr/bin/env python3
"""Fetch lyrics via the Genius API and store them under song_data/lyrics."""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

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
    / "Buckingham_Conspiracy_Song_List"
    / "Buckingham Conspiracy 3.0  SONG LIST.md"
)
LYRICS_DIR = DATA_ROOT / "song_data" / "lyrics"
GENIUS_API_BASE = "https://api.genius.com"
MARKER_PATTERN = re.compile(r"\^.*?\^")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0 Safari/537.36"
)


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


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


def ensure_token(options: argparse.Namespace) -> str:
    if options.token:
        return options.token
    token = os.getenv("GENIUS_ACCESS_TOKEN")
    if not token:
        raise SystemExit(
            "Set GENIUS_ACCESS_TOKEN or pass --token before running this script."
        )
    return token


def genius_request(path: str, token: str, params: Optional[Dict[str, str]] = None) -> Dict:
    url = f"{GENIUS_API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers, params=params, timeout=30)
    if response.status_code == 401:
        raise SystemExit("Genius rejected the token (401). Check your credentials.")
    response.raise_for_status()
    payload = response.json()
    return payload.get("response", {})


def search_song(title: str, artist: str, token: str) -> Optional[Dict]:
    query = f"{title} {artist}".strip()
    payload = genius_request("/search", token, params={"q": query})
    hits = payload.get("hits", [])
    if not hits:
        return None
    title_norm = normalize(title)
    artist_norm = normalize(artist)
    for hit in hits:
        result = hit.get("result", {})
        if not result:
            continue
        result_title = normalize(result.get("title", ""))
        result_artist = normalize(result.get("primary_artist", {}).get("name", ""))
        if title_norm and title_norm not in result_title:
            continue
        if artist_norm and artist_norm not in result_artist:
            continue
        return result
    return hits[0].get("result")


def fetch_lyrics_from_url(url: str) -> Optional[str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    containers = soup.select("div[data-lyrics-container='true']")
    if not containers:
        legacy = soup.select_one("div.lyrics")
        if legacy:
            containers = [legacy]
    if not containers:
        return None
    chunks = []
    for container in containers:
        text = container.get_text(separator="\n").strip()
        if text:
            chunks.append(text)
    lyrics = "\n\n".join(chunks).strip()
    return lyrics if lyrics else None


def determine_targets(options: argparse.Namespace, songs: Dict[str, Dict[str, str]]) -> List[str]:
    if options.song:
        if options.song not in songs:
            raise SystemExit(f"Song '{options.song}' was not found in the markdown list.")
        return [options.song]
    if not options.all_missing:
        raise SystemExit("Use --song or --all-missing to select which songs to fetch.")
    targets: List[str] = []
    for title in sorted(songs.keys()):
        destination = LYRICS_DIR / f"{title}.txt"
        if destination.exists() and not options.overwrite:
            continue
        targets.append(title)
        if options.limit and len(targets) >= options.limit:
            break
    return targets


def save_lyrics(title: str, lyrics: str) -> Path:
    LYRICS_DIR.mkdir(parents=True, exist_ok=True)
    destination = LYRICS_DIR / f"{title}.txt"
    destination.write_text(lyrics + "\n", encoding="utf-8")
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download lyrics via the Genius API into song_data/lyrics."
    )
    parser.add_argument("--song", help="Exact song title from the markdown catalog.")
    parser.add_argument(
        "--all-missing",
        action="store_true",
        help="Fetch lyrics for songs without existing .txt files.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum songs to download when using --all-missing.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate lyrics files even if they already exist.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to wait between API calls (default: 1s).",
    )
    parser.add_argument(
        "--token",
        help="Genius API access token (falls back to GENIUS_ACCESS_TOKEN).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    options = parser.parse_args()
    token = ensure_token(options)
    songs = parse_song_list()
    targets = determine_targets(options, songs)
    if not targets:
        print("No songs matched the requested criteria.")
        return 0

    success_count = 0
    for index, title in enumerate(targets, start=1):
        artist = songs[title]["artist"]
        print(f"[{index}/{len(targets)}] Fetching '{title}' ({artist or 'Unknown artist'})...")
        try:
            result = search_song(title, artist, token)
        except requests.HTTPError as exc:
            print(f"  ✗ HTTP error during search: {exc}")
            continue
        except requests.RequestException as exc:
            print(f"  ✗ Network error during search: {exc}")
            continue

        if not result:
            print("  ✗ No Genius matches found.")
            continue

        song_url = result.get("url")
        if not song_url:
            print("  ✗ Genius did not return a song URL.")
            continue

        try:
            lyrics = fetch_lyrics_from_url(song_url)
        except requests.HTTPError as exc:
            print(f"  ✗ HTTP error downloading lyrics page: {exc}")
            continue
        except requests.RequestException as exc:
            print(f"  ✗ Network error downloading lyrics page: {exc}")
            continue

        if not lyrics:
            print("  ✗ Could not extract lyrics from the page.")
            continue

        destination = save_lyrics(title, lyrics)
        print(f"  ✓ Saved to {display_path(destination)}")
        success_count += 1

        if index < len(targets):
            time.sleep(max(options.delay, 0))

    print(f"Done. {success_count} of {len(targets)} songs populated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
