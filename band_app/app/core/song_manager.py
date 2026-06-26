"""Song management module for band app - extracted from Streamlit app."""

import os
import re
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union


def resolve_data_root(base_dir: Path) -> Path:
    """Resolve the data root for bind-mounted storage."""
    data_root_env = os.getenv("BCH_DATA_DIR") or os.getenv("DATA_DIR")
    if not data_root_env:
        return base_dir
    data_root = Path(data_root_env).expanduser()
    if not data_root.is_absolute():
        data_root = base_dir / data_root
    return data_root.resolve()


# Base directory and data paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_ROOT = resolve_data_root(BASE_DIR)
SONGLIST_DIR = DATA_ROOT / "buckingham_conspiracy" / "songlist" / "Buckingham_Conspiracy_Song_List"
SONGLIST_MARKDOWN = SONGLIST_DIR / "Buckingham Conspiracy 3.0  SONG LIST.md"
SONGLIST_CSV = SONGLIST_DIR / "songlist_master.csv"

# CSV headers for song data
SONGLIST_CSV_HEADERS = [
    "title",
    "artist",
    "bpm",
    "has_horn",
    "energy_level",
    "is_jam_vehicle",
    "avg_length",
]


def parse_bool(value: Union[str, bool, None]) -> bool:
    """Parse various boolean representations."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "t"}


def calculate_song_duration(bpm: int) -> int:
    """Calculate estimated song duration based on BPM."""
    base_duration = 210  # 3.5 minutes in seconds
    return int(base_duration * (120 / max(bpm, 60)))


def derive_song_duration(bpm: int, avg_length_seconds: Optional[int]) -> int:
    """Use the provided average length, falling back to the BPM-derived duration."""
    if isinstance(avg_length_seconds, int) and avg_length_seconds > 0:
        return avg_length_seconds
    return calculate_song_duration(bpm)


def parse_avg_length_value(value: Union[str, int, float, None]) -> Optional[int]:
    """Parse the avg length value stored in the CSV into seconds."""
    if value is None:
        return None

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = int(value)
        return seconds if seconds > 0 else None

    raw = str(value).strip()
    if not raw:
        return None

    try:
        seconds = int(float(raw))
        return seconds if seconds > 0 else None
    except ValueError:
        return None


def split_minutes_seconds(seconds: Optional[int]) -> Tuple[int, int]:
    """Convert total seconds into (minutes, seconds)."""
    if not seconds or seconds <= 0:
        return 0, 0
    minutes = seconds // 60
    secs = seconds % 60
    return minutes, secs


def combine_avg_length(minutes: int, seconds: int) -> Optional[int]:
    """Turn a minutes/seconds pair into a total-second value."""
    total_seconds = max(0, int(minutes)) * 60 + max(0, int(seconds))
    return total_seconds if total_seconds > 0 else None


def load_song_list_from_csv(song_file: Path) -> Dict[str, Dict]:
    """Load songs from CSV file."""
    songs: Dict[str, Dict] = {}
    try:
        with open(song_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = (row.get("title") or "").strip()
                if not title:
                    continue
                artist = (row.get("artist") or "").strip()
                bpm_raw = (row.get("bpm") or "").strip()
                try:
                    bpm = int(float(bpm_raw))
                except (TypeError, ValueError):
                    bpm = 120
                energy_level = (row.get("energy_level") or "standard").strip().lower()
                energy_level = energy_level if energy_level in {"high", "standard", "low"} else "standard"
                has_horn = parse_bool(row.get("has_horn"))
                is_jam_vehicle = parse_bool(row.get("is_jam_vehicle"))
                avg_length_seconds = parse_avg_length_value(row.get("avg_length"))
                duration_seconds = derive_song_duration(bpm, avg_length_seconds)

                songs[title] = {
                    'bpm': bpm,
                    'duration': duration_seconds,
                    'has_horn': has_horn,
                    'energy_level': energy_level,
                    'is_jam_vehicle': is_jam_vehicle,
                    'artist': artist,
                    'avg_length': avg_length_seconds,
                    'raw_line': f"{title} ({bpm})",
                }
    except Exception as e:
        raise Exception(f"Error loading song list CSV: {e}")
    return songs


def load_song_list_from_markdown(song_file: Path) -> Dict[str, Dict]:
    """Load the complete song list from markdown file."""
    songs: Dict[str, Dict] = {}

    try:
        with open(song_file, 'r', encoding='utf-8') as f:
            content = f.read()

        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '(' in line:
                has_horn = '🎺' in line

                clean_line = re.sub(r'\^.*?\^', '', line)
                match = re.search(r'^(.+?)\s*\((\d+)\)', clean_line)
                if match:
                    name_with_artist = match.group(1).strip()
                    bpm = int(match.group(2))

                    song_name = name_with_artist
                    artist = ''
                    if ' - ' in name_with_artist:
                        song_name, artist = [part.strip() for part in name_with_artist.split(' - ', 1)]

                    duration_seconds = calculate_song_duration(bpm)

                    songs[song_name] = {
                        'bpm': bpm,
                        'duration': duration_seconds,
                        'has_horn': has_horn,
                        'energy_level': 'standard',
                        'is_jam_vehicle': False,
                        'artist': artist,
                        'avg_length': None,
                        'raw_line': line
                    }
    except Exception as e:
        raise Exception(f"Error loading song list: {e}")

    return songs


def load_song_list() -> Dict[str, Dict]:
    """Load the complete song list, preferring CSV when available."""
    if SONGLIST_CSV.exists():
        return load_song_list_from_csv(SONGLIST_CSV)
    return load_song_list_from_markdown(SONGLIST_MARKDOWN)


def save_song_list_csv(songs_data: Dict[str, Dict]) -> bool:
    """Save song metadata to CSV for editing outside the app."""
    try:
        SONGLIST_DIR.mkdir(parents=True, exist_ok=True)
        with open(SONGLIST_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=SONGLIST_CSV_HEADERS)
            writer.writeheader()
            for song_name in sorted(songs_data.keys()):
                song_info = songs_data[song_name]
                avg_length_value = song_info.get('avg_length')
                writer.writerow({
                    "title": song_name,
                    "artist": song_info.get('artist', ''),
                    "bpm": song_info.get('bpm', ''),
                    "has_horn": song_info.get('has_horn', False),
                    "energy_level": song_info.get('energy_level', 'standard'),
                    "is_jam_vehicle": song_info.get('is_jam_vehicle', False),
                    "avg_length": avg_length_value if avg_length_value is not None else '',
                })
        return True
    except Exception as e:
        raise Exception(f"Error saving song list CSV: {e}")


def save_song_list_markdown(songs_data: Dict[str, Dict]) -> bool:
    """Save the updated song list back to the markdown file."""
    try:
        SONGLIST_DIR.mkdir(parents=True, exist_ok=True)
        content = "# ****Buckingham Conspiracy 3.0 : SONG LIST ****  \n  \n#   \n"

        for song_name in sorted(songs_data.keys()):
            song_info = songs_data[song_name]
            markers = ""
            if song_info.get('has_horn'):
                markers += "^🎺 ^"

            display_name = song_name if not song_info.get('artist') else f"{song_name} - {song_info['artist']}"
            line = f"{display_name}{markers} ({song_info['bpm']})"
            content += line + "  \n"

        content += "  \n  \n#   \n  \n"

        with open(SONGLIST_MARKDOWN, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        raise Exception(f"Error saving song list: {e}")


def save_song_list(songs_data: Dict[str, Dict]) -> bool:
    """Save song data to CSV and markdown for compatibility."""
    try:
        csv_ok = save_song_list_csv(songs_data)
        md_ok = save_song_list_markdown(songs_data)
        return csv_ok and md_ok
    except Exception:
        return False


def get_song_stats(songs_data: Dict[str, Dict]) -> Dict[str, Union[int, float]]:
    """Calculate song statistics."""
    if not songs_data:
        return {}

    total_songs = len(songs_data)
    jam_vehicles = len([s for s in songs_data.values() if s.get('is_jam_vehicle')])
    avg_bpm = sum(s['bpm'] for s in songs_data.values()) / len(songs_data)
    horn_songs = len([s for s in songs_data.values() if s.get('has_horn')])

    energy_counts = {}
    for song in songs_data.values():
        energy = song.get('energy_level', 'standard')
        energy_counts[energy] = energy_counts.get(energy, 0) + 1

    return {
        'total_songs': total_songs,
        'jam_vehicles': jam_vehicles,
        'avg_bpm': round(avg_bpm, 1),
        'horn_songs': horn_songs,
        'energy_distribution': energy_counts
    }