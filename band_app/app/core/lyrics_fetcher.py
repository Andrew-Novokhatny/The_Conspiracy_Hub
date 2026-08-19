"""Lyrics fetching engine using Genius API / search with clean text parsing."""

from __future__ import annotations

import os
import re
import urllib.parse
from typing import Dict, Optional, Tuple, Any
import requests
from bs4 import BeautifulSoup

GENIUS_API_BASE = "https://api.genius.com"
GENIUS_SEARCH_URL = "https://genius.com/api/search/multi"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 12


def clean_scraped_lyrics(raw_lyrics: str) -> str:
    """Clean scraped lyrics, removing Genius metadata preamble and embed tags."""
    if not raw_lyrics:
        return ""

    lines = raw_lyrics.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    cleaned_lines = []
    found_start = False

    for line in lines:
        stripped = line.strip()
        if not found_start:
            # Check for section markers like [Intro], [Verse 1], [Chorus]
            if re.match(r"^\s*\[.+?\]", stripped):
                found_start = True
                cleaned_lines.append(stripped)
            elif "Lyrics" in stripped and not found_start:
                continue
            elif re.search(r"\d+\s+Contributors|Translations|Read More", stripped, re.IGNORECASE):
                continue
            elif stripped and not re.search(r"Contributors|Translations|Lyrics|Embed", stripped, re.IGNORECASE):
                found_start = True
                cleaned_lines.append(stripped)
        else:
            # Strip Genius bottom embed text like '144Embed'
            if re.search(r"\d*Embed\s*$", stripped):
                clean_end = re.sub(r"\d*Embed\s*$", "", stripped).strip()
                if clean_end:
                    cleaned_lines.append(clean_end)
                continue
            cleaned_lines.append(stripped)

    # Trim leading/trailing blank lines
    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    return "\n".join(cleaned_lines).strip()


def search_genius_song_url(title: str, artist: str = "") -> Optional[Tuple[str, str, str]]:
    """Search Genius for a song URL. Returns (song_url, matched_title, matched_artist) or None."""
    query = f"{title} {artist}".strip()
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    
    # 1. Try authenticated API if token exists
    token = os.getenv("GENIUS_ACCESS_TOKEN")
    if token:
        try:
            auth_headers = {**headers, "Authorization": f"Bearer {token}"}
            resp = requests.get(
                f"{GENIUS_API_BASE}/search",
                headers=auth_headers,
                params={"q": query},
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 200:
                hits = resp.json().get("response", {}).get("hits", [])
                if hits:
                    hit = hits[0].get("result", {})
                    return hit.get("url"), hit.get("title", title), hit.get("primary_artist", {}).get("name", artist)
        except Exception:
            pass

    # 2. Fall back to public search endpoint
    try:
        url = f"{GENIUS_SEARCH_URL}?per_page=5&q={urllib.parse.quote(query)}"
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            sections = data.get("response", {}).get("sections", [])
            for sec in sections:
                if sec.get("type") == "song":
                    hits = sec.get("hits", [])
                    if hits:
                        hit = hits[0].get("result", {})
                        return hit.get("url"), hit.get("title", title), hit.get("primary_artist", {}).get("name", artist)
    except Exception as e:
        print(f"Genius public search error for '{query}': {e}")

    return None


def fetch_lyrics_from_url(url: str) -> Optional[str]:
    """Download HTML from Genius song page and extract lyrics."""
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        containers = soup.select("div[data-lyrics-container='true']")
        if not containers:
            legacy = soup.select_one("div.lyrics")
            if legacy:
                containers = [legacy]

        if not containers:
            return None

        chunks = []
        for container in containers:
            for br in container.find_all("br"):
                br.replace_with("\n")
            text = container.get_text().strip()
            if text:
                chunks.append(text)

        raw_lyrics = "\n\n".join(chunks).strip()
        return clean_scraped_lyrics(raw_lyrics)
    except Exception as e:
        print(f"Error fetching lyrics from URL {url}: {e}")
        return None


def fetch_lyrics_online(title: str, artist: str = "") -> Dict[str, Any]:
    """High-level function to fetch lyrics for a song title & artist.
    Returns:
        {
            'success': bool,
            'lyrics': str,
            'matched_title': str,
            'matched_artist': str,
            'source_url': str,
            'error': str or None
        }
    """
    search_res = search_genius_song_url(title, artist)
    if not search_res or not search_res[0]:
        return {
            'success': False,
            'lyrics': '',
            'matched_title': '',
            'matched_artist': '',
            'source_url': '',
            'error': f"No Genius search results found for '{title}'" + (f" by {artist}" if artist else "")
        }

    url, matched_title, matched_artist = search_res
    lyrics = fetch_lyrics_from_url(url)
    if not lyrics:
        return {
            'success': False,
            'lyrics': '',
            'matched_title': matched_title,
            'matched_artist': matched_artist,
            'source_url': url,
            'error': f"Found Genius page ({matched_title}) but could not extract lyrics text."
        }

    return {
        'success': True,
        'lyrics': lyrics,
        'matched_title': matched_title,
        'matched_artist': matched_artist,
        'source_url': url,
        'error': None
    }
