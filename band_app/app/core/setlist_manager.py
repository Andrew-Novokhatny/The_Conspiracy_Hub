"""Setlist management module for band app - extracted from Streamlit app."""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from .song_manager import DATA_ROOT


# Data paths for setlists
SETLISTS_DIR = DATA_ROOT / "buckingham_conspiracy" / "setlists"


def load_previous_setlists() -> List[Dict]:
    """Load all previous setlists"""
    setlists_dir = SETLISTS_DIR
    setlists = []

    try:
        for venue_dir in os.listdir(setlists_dir):
            venue_path = os.path.join(setlists_dir, venue_dir)
            if os.path.isdir(venue_path):
                for file in os.listdir(venue_path):
                    if file.endswith('.md'):
                        file_path = os.path.join(venue_path, file)
                        setlist_data = parse_setlist_file(file_path, venue_dir)
                        if setlist_data:
                            setlists.append(setlist_data)
    except Exception as e:
        raise Exception(f"Error loading setlists: {e}")

    def sort_key(x):
        try:
            return datetime.strptime(x['date'], "%m/%d/%y")
        except ValueError:
            return datetime.min

    return sorted(setlists, key=sort_key, reverse=True)


def parse_setlist_file(file_path: str, venue_dir: str) -> Dict:
    """Parse a setlist markdown file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract venue and date from directory name
        venue_match = re.search(r'(.+?) Setlist \((\d+)\)', venue_dir)
        if venue_match:
            venue = venue_match.group(1)
            date_str = venue_match.group(2)
            # Convert date format (e.g., 030725 -> 03/07/25)
            if len(date_str) == 6:
                date = f"{date_str[:2]}/{date_str[2:4]}/{date_str[4:]}"
            else:
                date = date_str
        else:
            venue = venue_dir
            date = "Unknown"

        # Parse sets
        sets = {'set1': [], 'set2': [], 'set3': []}
        current_set = None

        for line in content.split('\n'):
            line = line.strip()
            if 'SET 1' in line:
                current_set = 'set1'
            elif 'SET 2' in line:
                current_set = 'set2'
            elif 'SET 3' in line:
                current_set = 'set3'
            elif current_set and line and not line.startswith('#'):
                # Extract song name and BPM - Fixed regex to capture full song name
                song_match = re.search(r'^(.+?)\s*(?:\((\d+)\))?$', line)
                if song_match:
                    song_name = song_match.group(1).strip()
                    bpm = song_match.group(2) if song_match.group(2) else None

                    # Clean up song name
                    song_name = re.sub(r'\*\*\*\*.*?\*\*\*\*', '', song_name)
                    song_name = re.sub(r'\^.*?\^', '', song_name)
                    song_name = re.sub(r'[🎺🥁#]', '', song_name)
                    song_name = song_name.strip()

                    if song_name and song_name.lower() != 'empty':
                        # Check for duplicates - only add if not already in the set
                        existing_songs = [s['name'] for s in sets[current_set]]
                        if song_name not in existing_songs:
                            sets[current_set].append({
                                'name': song_name,
                                'bpm': int(bpm) if bpm else None,
                                'raw_line': line
                            })

        return {
            'venue': venue,
            'date': date,
            'sets': sets,
            'file_path': file_path
        }
    except Exception as e:
        raise Exception(f"Error parsing setlist {file_path}: {e}")


def save_setlist_to_file(setlist_data: Dict) -> bool:
    """Save setlist changes back to the markdown file"""
    try:
        file_path = setlist_data['file_path']
        venue = setlist_data['venue']
        date = setlist_data['date']
        sets = setlist_data['sets']

        # Create the markdown content
        content = f"# ****{venue} Setlist ({date})****  \n  \n"
        content += "# - Travis sit-in  \n🎺 - Horn  \n  \n"

        # Add each set
        for set_num in [1, 2, 3]:
            set_key = f"set{set_num}"
            set_songs = sets.get(set_key, [])

            if set_num == 1:
                content += "# ****—SET 1****  \n"
            elif set_num == 2:
                content += "#   \n# ****—-SET 2****  \n"
            elif set_num == 3:
                content += "#   \n# ****—-SET 3****  \n"

            for song in set_songs:
                if song['bpm']:
                    content += f"{song['name']} ({song['bpm']})  \n"
                else:
                    content += f"{song['name']}  \n"

            if set_num < 3:
                content += "#   \n"

        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        raise Exception(f"Error saving setlist: {e}")


def format_duration(seconds: int) -> str:
    """Format duration in MM:SS format"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def get_energy_emoji(energy_level: str) -> str:
    """Get emoji for energy level"""
    energy_emojis = {
        'high': '🔥',      # Fire for high energy
        'standard': '',    # Star for standard energy
        'low': '💤'        # Sleeping for low energy
    }
    return energy_emojis.get(energy_level, '')


def get_energy_options() -> List[str]:
    """Get available energy level options"""
    return ['high', 'standard', 'low']


def calculate_set_timing(songs: List[str], song_data: Dict, break_duration: int = 0) -> Tuple[int, str]:
    """Calculate total timing for a set including break"""
    total_seconds = 0
    for song in songs:
        if song in song_data:
            total_seconds += song_data[song]['duration']

    # Add break time
    total_with_break = total_seconds + (break_duration * 60)

    return total_seconds, format_duration(total_with_break)


def human_readable_date(date_str: str) -> str:
    """Convert MM/DD/YY input into a verbose date whenever possible."""
    try:
        parsed = datetime.strptime(date_str, "%m/%d/%y")
        return parsed.strftime("%B %d, %Y")
    except ValueError:
        return date_str


def build_setlist_markdown(venue: str, date: str, setlist: Dict[str, List[str]], songs_data: Dict[str, Dict], set_durations: Dict[str, str], total_show: str) -> str:
    """Build markdown representation of a setlist for export"""
    friendly_date = human_readable_date(date)
    header = f"## 🎸 {venue} ({friendly_date})"
    lines = [header, ""]

    for set_num in range(1, 4):
        set_key = f"set{set_num}"
        songs = setlist.get(set_key, [])
        lines.append(f"#### **Set {set_num}**")
        lines.append("| # | Song | BPM | Duration |")
        lines.append("|---|------|-----|----------|")

        for idx, song in enumerate(songs, 1):
            song_info = songs_data.get(song, {})
            bpm = song_info.get('bpm', '---')
            duration = song_info.get('duration', 0)
            duration_str = format_duration(duration) if duration else '---'
            lines.append(f"| {idx} | {song} | {bpm} | {duration_str} |")

        # Add set timing
        set_duration_key = f"set{set_num}_duration"
        set_duration = set_durations.get(set_duration_key, "---")
        lines.append(f"| | **Set {set_num} Total** | | **{set_duration}** |")
        lines.append("")

    lines.append(f"**Total Show: {total_show}**")
    return "\n".join(lines)


def create_setlist_export_data(venue: str, date: str, setlist: Dict[str, List[str]]) -> Dict:
    """Create exportable JSON data for a setlist"""
    return {
        "venue": venue,
        "date": date,
        "setlist": {
            "set1": setlist.get("set1", []),
            "set2": setlist.get("set2", []),
            "set3": setlist.get("set3", [])
        },
        "created_at": datetime.now().isoformat(),
        "format_version": "1.0"
    }


def load_setlist_from_json(json_data: str) -> Optional[Dict]:
    """Load setlist from JSON string"""
    try:
        loaded = json.loads(json_data)
        # Validate expected structure
        if "setlist" in loaded and isinstance(loaded["setlist"], dict):
            return {
                "setlist": {
                    "set1": loaded["setlist"].get("set1", []),
                    "set2": loaded["setlist"].get("set2", []),
                    "set3": loaded["setlist"].get("set3", []),
                },
                "venue": loaded.get("venue", ""),
                "date": loaded.get("date", "")
            }
        return None
    except json.JSONDecodeError:
        return None


def search_setlists_by_song(song_name: str) -> List[Dict]:
    """Find all setlists that contain a specific song"""
    setlists = load_previous_setlists()
    matching_setlists = []

    song_name_lower = song_name.lower()

    for setlist in setlists:
        for set_key, songs in setlist['sets'].items():
            for song in songs:
                if song_name_lower in song['name'].lower():
                    matching_setlists.append({
                        'setlist': setlist,
                        'set': set_key,
                        'song': song
                    })
                    break

    return matching_setlists