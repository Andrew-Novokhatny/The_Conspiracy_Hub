"""Lyrics management module for band app - extracted from Streamlit app."""

import html
import re
from pathlib import Path
from typing import List

from .song_manager import DATA_ROOT


# Data paths for lyrics
SONG_DATA_DIR = DATA_ROOT / "buckingham_conspiracy" / "song_data"
LYRICS_DIR = SONG_DATA_DIR / "lyrics"

# Pattern to match section labels like [Chorus], [Verse 1], etc.
SECTION_LABEL_PATTERN = re.compile(r"^\s*\[.+?\]\s*$")


def load_available_lyrics() -> List[str]:
    """Load list of available lyrics files"""
    try:
        lyrics_files = []
        if LYRICS_DIR.exists():
            for file in LYRICS_DIR.glob("*.txt"):
                lyrics_files.append(file.stem)  # Get filename without extension
        return sorted(lyrics_files)
    except Exception as e:
        raise Exception(f"Error loading lyrics files: {e}")


def load_lyrics_content(song_name: str) -> str:
    """Load lyrics content from file"""
    try:
        lyrics_file = LYRICS_DIR / f"{song_name}.txt"
        if lyrics_file.exists():
            with open(lyrics_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                content = content.replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ')
                return content.strip()
        else:
            return f"Lyrics file for '{song_name}' not found."
    except Exception as e:
        return f"Error loading lyrics: {e}"


def format_lyrics_for_display(content: str) -> str:
    """Ensure section headers have clean padding and render bold in HTML without any leading empty space."""
    if not content:
        return ""

    raw_lines = content.replace('\r\n', '\n').replace('\r', '\n').replace('\xa0', ' ').split('\n')
    
    # Strip leading empty lines before first content line
    start_idx = 0
    while start_idx < len(raw_lines) and not raw_lines[start_idx].strip():
        start_idx += 1
    raw_lines = raw_lines[start_idx:]

    formatted_lines: List[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if SECTION_LABEL_PATTERN.match(stripped):
            # Only add a blank spacer line if there are already preceding non-empty lines
            if formatted_lines and formatted_lines[-1] != "":
                formatted_lines.append("")
            formatted_lines.append(f"<strong>{html.escape(stripped)}</strong>")
        else:
            formatted_lines.append(html.escape(line))

    # Clean leading and trailing empty lines
    while formatted_lines and formatted_lines[0] == "":
        formatted_lines.pop(0)
    while formatted_lines and formatted_lines[-1] == "":
        formatted_lines.pop()

    return "<br/>".join(formatted_lines)


def save_lyrics_content(song_name: str, content: str) -> bool:
    """Save lyrics content to file."""
    try:
        LYRICS_DIR.mkdir(parents=True, exist_ok=True)
        lyrics_file = LYRICS_DIR / f"{song_name}.txt"
        with open(lyrics_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        raise Exception(f"Error saving lyrics: {e}")


def delete_lyrics_file(song_name: str) -> bool:
    """Delete a lyrics file."""
    try:
        lyrics_file = LYRICS_DIR / f"{song_name}.txt"
        if lyrics_file.exists():
            lyrics_file.unlink()
            return True
        return False
    except Exception as e:
        raise Exception(f"Error deleting lyrics file: {e}")


def search_lyrics(query: str) -> List[str]:
    """Search for songs that have lyrics containing the query."""
    matching_songs = []
    available_lyrics = load_available_lyrics()

    query_lower = query.lower()

    for song_name in available_lyrics:
        lyrics_content = load_lyrics_content(song_name)
        if query_lower in lyrics_content.lower():
            matching_songs.append(song_name)

    return matching_songs