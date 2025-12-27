#!/usr/bin/env python3
"""
Script to add artist information to the song list
"""

# Artist mapping
ARTISTS = {
    "1612": "Vulfpeck",
    "2nd Red Barn on the Right": "From Good Homes",
    "After Midnight": "JJ Cale",
    "Another Brick in the Wall": "Pink Floyd",
    "Bertha": "Grateful Dead",
    "Can't U See": "Marshall Tucker Band",
    "Chameleon": "Herbie Hancock",
    "Cissy Strut": "The Meters",
    "Cities": "Talking Heads",
    "Cocaine": "JJ Cale",
    "Could You Be Loved": "Bob Marley",
    "DWBWID": "Delvin Lamar Organ Trio",
    "Dancing in the Moonlight": "King Harvest",
    "Deal": "Grateful Dead",
    "Down Under": "Men at Work",
    "Electric Avenue": "Eddy Grant",
    "Elizabeth": "Goose",
    "Express Urself": "Charles Wright & the Watts 103rd Street Rhythm Band",
    "Fire on the Mountain": "Grateful Dead",
    "Ghostbusters": "Ray Parker Jr.",
    "Green Onions": "Booker T. & the M.G.'s",
    "Green River": "Creedence Clearwater Revival",
    "Hard to Handle": "The Black Crowes",
    "Higher Ground": "Stevie Wonder",
    "Hollywood Swinging": "Kool & The Gang",
    "I'm a Ram": "Al Green",
    "In the Meantime": "Spacehog",
    "It's a Bunch": "Spafford",
    "Jumping Jack Flash": "The Rolling Stones",
    "Leave the Light On": "Spafford",
    "Little L": "Jamiroquai",
    "Mary Janes Last Dance": "Tom Petty",
    "Midnight Rider": "The Allman Brothers Band",
    "Miss You": "The Rolling Stones",
    "No Rain": "Blind Melon",
    "Officer": "Slightly Stoopid",
    "Owner of a Lonely Heart": "Yes",
    "Poster Child": "Red Hot Chili Peppers",
    "Praise U": "Fatboy Slim",
    "Pumped Up Kicks": "Foster the People",
    "Remedy": "The Black Crowes",
    "Shakedown Street": "Grateful Dead",
    "Southbound": "The Allman Brothers Band",
    "Superstition": "Stevie Wonder",
    "Take Me to the River": "Al Green",
    "Thank U": "Sly and the Family Stone",
    "Time": "Pink Floyd",
    "Use Me": "Bill Withers",
    "WS Walcott": "The Band",
    "When My Train Pulls In": "Gary Clark Jr.",
    "White Wedding": "Billy Idol",
    "Wish I Knew You": "The Revivalists"
}

import os
import re
from pathlib import Path

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

# Read the file
file_path = (
    DATA_ROOT
    / "songlist"
    / "Buckingham_Conspiracy_Song_List"
    / "Buckingham Conspiracy 3.0  SONG LIST.md"
)
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Parse and update
lines = content.split('\n')
new_lines = []

for line in lines:
    line_stripped = line.strip()
    if line_stripped and not line_stripped.startswith('#') and '(' in line_stripped:
        # Extract song name
        match = re.search(r'^(.+?)(?:\^.*?\^)*\s*\((\d+)\)', line_stripped)
        if match:
            song_name_raw = match.group(1).strip()
            bpm = match.group(2)
            
            # Clean song name
            song_name = re.sub(r'\^.*?\^', '', song_name_raw).strip()
            
            # Get artist
            artist = ARTISTS.get(song_name, "Unknown Artist")
            
            # Rebuild line with artist
            # Format: Song Name - Artist^markers^ (BPM)
            markers = ''.join(re.findall(r'\^.*?\^', line_stripped))
            new_line = f"{song_name} - {artist}{markers} ({bpm})"
            new_lines.append(new_line + "  ")
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

# Write back
new_content = '\n'.join(new_lines)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Updated {len(ARTISTS)} songs with artist information!")
