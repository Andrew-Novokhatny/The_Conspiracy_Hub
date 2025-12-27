import streamlit as st
import os
import re
import json
import html
import sys
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path

# Get the base directory (parent of src/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure the repository root is on sys.path so custom components can be imported
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from components.st_musicxml_viewer import musicxml_viewer
SONGLIST_DIR = BASE_DIR / "songlist" / "Buckingham Conspiracy 3.0  SONG LIST"
SETLISTS_DIR = BASE_DIR / "setlists"
SONG_DATA_DIR = BASE_DIR / "song_data"
LYRICS_DIR = SONG_DATA_DIR / "lyrics"
TABS_DIR = SONG_DATA_DIR / "tabs"
TABS_RAW_JSON_DIR = TABS_DIR / "raw_json"
TABS_MUSICXML_DIR = TABS_DIR / "musicxml"
SECTION_LABEL_PATTERN = re.compile(r"^\s*\[.+?\]\s*$")
TAB_DURATION_MAP = {
    'w': 4.0,   # whole note
    'h': 2.0,   # half note
    'q': 1.0,   # quarter note
    'e': 0.5,   # eighth note
    's': 0.25,  # sixteenth note
}
TAB_BUILDER_SAMPLE = (
    "C4:q E4:q G4:q C5:q\n"
    "rest:h C4:q G3:q\n"
    "C4+E4+G4:h rest:h"
)

def load_song_list() -> Dict[str, Dict]:
    """Load the complete song list from markdown file"""
    song_file = SONGLIST_DIR / "Buckingham Conspiracy 3.0  SONG LIST.md"
    songs = {}
    
    try:
        with open(song_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '(' in line:
                has_horn = '🎺' in line
                has_vocals = '🥁' in line
                
                clean_line = re.sub(r'\^.*?\^', '', line)
                match = re.search(r'^(.+?)\s*\((\d+)\)', clean_line)
                if match:
                    name_with_artist = match.group(1).strip()
                    bpm = int(match.group(2))
                    
                    song_name = name_with_artist
                    artist = ''
                    if ' - ' in name_with_artist:
                        song_name, artist = [part.strip() for part in name_with_artist.split(' - ', 1)]
                    
                    base_duration = 210  # 3.5 minutes in seconds
                    duration_seconds = int(base_duration * (120 / max(bpm, 60)))
                    
                    songs[song_name] = {
                        'bpm': bpm,
                        'duration': duration_seconds,
                        'has_horn': has_horn,
                        'has_vocals': has_vocals,
                        'energy_level': 'standard',
                        'is_jam_vehicle': False,
                        'artist': artist,
                        'raw_line': line
                    }
    except Exception as e:
        st.error(f"Error loading song list: {e}")
    
    return songs

def save_song_list(songs_data: Dict[str, Dict]):
    """Save the updated song list back to the markdown file"""
    song_file = SONGLIST_DIR / "Buckingham Conspiracy 3.0  SONG LIST.md"
    
    try:
        content = "# ****Buckingham Conspiracy 3.0 : SONG LIST ****  \n  \n#   \n"
        
        for song_name in sorted(songs_data.keys()):
            song_info = songs_data[song_name]
            markers = ""
            if song_info.get('has_horn'):
                markers += "^🎺 ^"
            if song_info.get('has_vocals'):
                markers += "^🥁^"
            
            display_name = song_name if not song_info.get('artist') else f"{song_name} - {song_info['artist']}"
            line = f"{display_name}{markers} ({song_info['bpm']})"
            content += line + "  \n"
        
        content += "  \n  \n#   \n  \n"
        
        with open(song_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        st.error(f"Error saving song list: {e}")
        return False

# Page configuration
st.set_page_config(
    page_title="🎸 Buckingham Conspiracy Hub",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom CSS for band styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&display=swap');

:root {
    --bg-deep: #0c0f15;
    --bg-panel: #141821;
    --bg-raised: #1d2230;
    --bg-highlight: #3f4863;
    --border-subtle: rgba(255,255,255,0.08);
    --text-primary: #ffffff;
    --text-muted: #f0f2f5;
    --accent-primary: #00d4d8;
    --accent-secondary: #41ffe2;
    --accent-soft: rgba(0,212,216,0.15);
    --shadow-soft: 0 25px 40px rgba(0,0,0,0.35);
}

body, .stApp {
    background: radial-gradient(circle at top, #131722 0%, #0c0f15 60%);
    color: var(--text-primary);
    font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
}

[data-testid="stAppViewContainer"] > .main {
    background: transparent;
}

header[data-testid="stHeader"] {
    background: var(--bg-deep);
    border-bottom: 1px solid var(--border-subtle);
    box-shadow: none;
}

.main-header {
    background: linear-gradient(120deg, rgba(33, 41, 57, 0.95), rgba(16, 19, 27, 0.9));
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 1.4rem;
    text-align: center;
    margin-bottom: 2.5rem;
    box-shadow: var(--shadow-soft);
}

.main-header h1 {
    margin-bottom: 0.4rem;
    letter-spacing: 0.08em;
}

section[data-testid="stSidebar"] > div {
    background: var(--bg-panel);
    border-right: 1px solid var(--border-subtle);
}

section[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

.song-card,
.edit-song-form {
    background: var(--bg-raised);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid var(--border-subtle);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
}

.song-card {
    margin: 0.6rem 0;
    border-left: 3px solid var(--accent-primary);
}

.metric-card {
    background: var(--bg-raised);
    border-radius: 14px;
    padding: 1.25rem;
    text-align: center;
    border: 1px solid var(--border-subtle);
    box-shadow: var(--shadow-soft);
}

.metric-title {
    font-size: 0.85rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.metric-value {
    font-size: 2rem;
    font-weight: 600;
    color: var(--accent-secondary);
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.02);
    border-radius: 14px;
    padding: 0.25rem;
    border: 1px solid var(--border-subtle);
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: var(--text-muted);
    font-size: 1rem;
    font-weight: 500;
    border-radius: 12px;
    padding: 0.5rem 1.25rem;
}

.stTabs [aria-selected="true"] {
    background: var(--bg-raised);
    color: var(--text-primary);
    border: 1px solid var(--border-subtle);
    box-shadow: var(--shadow-soft);
}

.lyrics-container,
.lyrics-container-mobile {
    background: linear-gradient(150deg, rgba(19,23,34,0.95), rgba(11,14,20,0.95));
    border-radius: 18px;
    padding: 2rem;
    border: 1px solid var(--border-subtle);
    box-shadow: var(--shadow-soft);
    min-height: 500px;
    max-height: 70vh;
    overflow-y: auto;
}

.lyrics-container-mobile {
    padding: 1.4rem;
    min-height: 420px;
}

.lyrics-container-fullscreen {
    max-height: none;
    min-height: 80vh;
    height: 80vh;
    width: 100%;
    border-radius: 0;
    padding: 2.2rem;
}

.lyrics-text,
.lyrics-text-mobile,
.lyrics-text-tablet,
.lyrics-text-desktop {
    color: #f1f5f9;
    font-size: 1.15rem;
    line-height: 2.1;
    font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
    white-space: pre-wrap;
    letter-spacing: 0.04em;
}

.lyrics-text-mobile {
    font-size: 1.25rem;
}

.lyrics-text-tablet {
    font-size: 1.35rem;
}

.lyrics-title {
    color: var(--accent-secondary);
    font-size: 1.8rem;
    letter-spacing: 0.3em;
    text-align: center;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
}

.lyrics-container::-webkit-scrollbar,
.lyrics-container-mobile::-webkit-scrollbar {
    width: 10px;
}

.lyrics-container::-webkit-scrollbar-track,
.lyrics-container-mobile::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
}

.lyrics-container::-webkit-scrollbar-thumb,
.lyrics-container-mobile::-webkit-scrollbar-thumb {
    background: var(--accent-primary);
    border-radius: 10px;
}

.lyrics-container::-webkit-scrollbar-thumb:hover,
.lyrics-container-mobile::-webkit-scrollbar-thumb:hover {
    background: var(--accent-secondary);
}

.stButton button,
.stDownloadButton button,
.stFileUploader label {
    background: var(--bg-raised);
    color: var(--text-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 0.65rem 1.5rem;
    font-weight: 600;
    box-shadow: var(--shadow-soft);
}

.stButton button:hover,
.stDownloadButton button:hover {
    background: var(--bg-highlight);
    transform: translateY(-1px);
    box-shadow: var(--shadow-soft);
}

.stButton button[kind="primary"],
.stButton button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
    color: #0c1118;
    border: none;
    box-shadow: 0 12px 25px rgba(0,212,216,0.25);
}

.stButton button[kind="primary"]:hover,
.stButton button[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 18px 30px rgba(0,212,216,0.4);
}

.stFormSubmitButton button {
    background: var(--bg-raised);
    color: var(--text-primary);
    border: 1px solid var(--border-subtle);
    box-shadow: var(--shadow-soft);
}

.stFormSubmitButton button:hover {
    background: var(--bg-highlight);
}

input,
textarea,
select,
.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stTextArea textarea,
.stDateInput input,
.stTimeInput input {
    background: var(--bg-panel);
    color: var(--text-primary);
    border-radius: 12px;
    border: 1px solid var(--border-subtle);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03);
}

input::placeholder,
textarea::placeholder,
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: rgba(196, 206, 221, 0.6);
    opacity: 1;
}

.stNumberInput button {
    background: var(--bg-highlight);
    border: none;
    color: var(--text-primary);
}

.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus,
.stSelectbox div[data-baseweb="select"] > div:focus,
.stDateInput input:focus,
.stTimeInput input:focus {
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 1px var(--accent-primary);
}

.stCheckbox {
    color: var(--text-primary);
}

.stCheckbox label {
    color: var(--text-primary) !important;
}

.stCheckbox input[type="checkbox"] {
    border: 2px solid var(--text-primary);
}

.streamlit-expanderHeader {
    font-size: 1.2rem;
    font-weight: 600;
}

.streamlit-expanderHeader p {
    font-size: 1.2rem;
}

label,
.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stDateInput label,
.stTimeInput label {
    color: #ffffff !important;
    font-weight: 600;
    font-size: 1rem;
}

.stMarkdown a {
    color: var(--accent-secondary);
}

.streamlit-expanderHeader {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
}

.control-label {
    color: var(--text-primary);
    font-weight: 600;
    font-size: 0.95rem;
    letter-spacing: 0.04em;
    margin-bottom: 0.35rem;
}

.inline-hint {
    background: linear-gradient(120deg, rgba(33, 41, 57, 0.7), rgba(10, 13, 19, 0.95));
    color: var(--text-muted);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 0.8rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.03);
}

.inline-hint span {
    font-size: 1.3rem;
}

.inline-hint p {
    margin: 0;
}

@media (max-width: 900px) {
    .main-header {
        padding: 1.1rem;
        margin-bottom: 1.75rem;
    }

    .main-header h1 {
        font-size: 1.6rem;
        letter-spacing: 0.06em;
    }

    .main-header p {
        font-size: 0.95rem;
    }

    .metric-card {
        padding: 1rem;
    }

    div[data-testid="stHorizontalBlock"] {
        flex-direction: column;
        gap: 0.75rem;
    }

    div[data-testid="stHorizontalBlock"] > div {
        width: 100% !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        flex-wrap: wrap;
    }

    .lyrics-container,
    .lyrics-container-mobile {
        max-height: none;
    }

    .lyrics-container-fullscreen {
        min-height: 75vh;
        height: 75vh;
        padding: 1.6rem;
    }
}
</style>
""", unsafe_allow_html=True)


def render_control_label(label_text: str):
    """Render a consistent label style for Streamlit inputs."""
    safe = html.escape(label_text.strip()) if label_text else ""
    if safe:
        st.markdown(f"<p class='control-label'>{safe}</p>", unsafe_allow_html=True)


def styled_selectbox(label: str, options, *, label_visibility: str = "collapsed", **kwargs):
    """Selectbox with themed label treatment."""
    plain_label = (label or "").rstrip(':').strip()
    render_control_label(plain_label)
    internal_label = label if label.endswith(':') else f"{label}:"
    return st.selectbox(internal_label, options, label_visibility=label_visibility, **kwargs)

# Initialize session state for setlist builder
if 'current_setlist' not in st.session_state:
    st.session_state.current_setlist = {
        'set1': [],
        'set2': [],
        'set3': []
    }

if 'setlist_metadata' not in st.session_state:
    st.session_state.setlist_metadata = {
        'venue': '',
        'date': datetime.now().strftime('%m/%d/%y'),
        'set_breaks': {'set1_break': 15, 'set2_break': 15}
    }

if 'songs_data' not in st.session_state:
    st.session_state.songs_data = None

if 'editing_song' not in st.session_state:
    st.session_state.editing_song = None

if 'editing_setlist' not in st.session_state:
    st.session_state.editing_setlist = None

if 'edited_setlist_data' not in st.session_state:
    st.session_state.edited_setlist_data = None

if 'selected_lyrics_song' not in st.session_state:
    st.session_state.selected_lyrics_song = None

if 'lyrics_fullscreen' not in st.session_state:
    st.session_state.lyrics_fullscreen = False

if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'Desktop'

if 'tab_builder_measure_input' not in st.session_state:
    st.session_state.tab_builder_measure_input = TAB_BUILDER_SAMPLE

# Utility functions

# Utility functions

# Utility functions
def load_available_lyrics() -> List[str]:
    """Load list of available lyrics files"""
    try:
        lyrics_files = []
        if LYRICS_DIR.exists():
            for file in LYRICS_DIR.glob("*.txt"):
                lyrics_files.append(file.stem)  # Get filename without extension
        return sorted(lyrics_files)
    except Exception as e:
        st.error(f"Error loading lyrics files: {e}")
        return []

def load_lyrics_content(song_name: str) -> str:
    """Load lyrics content from file"""
    try:
        lyrics_file = LYRICS_DIR / f"{song_name}.txt"
        if lyrics_file.exists():
            with open(lyrics_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"Lyrics file for '{song_name}' not found."
    except Exception as e:
        return f"Error loading lyrics: {e}"


def format_lyrics_for_display(content: str) -> str:
    """Ensure section headers have padding and render bold in HTML."""
    formatted_lines: List[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if SECTION_LABEL_PATTERN.match(stripped):
            if formatted_lines and formatted_lines[-1] != "":
                formatted_lines.append("")
            formatted_lines.append(f"<strong>{html.escape(stripped)}</strong>")
        else:
            formatted_lines.append(html.escape(line))
    return "<br/>".join(formatted_lines)

def load_available_tabs() -> List[str]:
    """Load list of available tab files"""
    try:
        tab_files: set[str] = set()
        if TABS_MUSICXML_DIR.exists():
            for file in TABS_MUSICXML_DIR.glob("*"):
                if file.is_file():
                    tab_files.add(file.name)
        if TABS_DIR.exists():
            for file in TABS_DIR.glob("*"):
                if file.is_file():
                    tab_files.add(file.name)
        return sorted(tab_files)
    except Exception as e:
        st.error(f"Error loading tab files: {e}")
        return []

def resolve_tab_file(filename: str) -> Path | None:
    """Find the actual path for a tab filename across supported directories"""
    search_paths = [TABS_MUSICXML_DIR, TABS_DIR, TABS_RAW_JSON_DIR]
    for directory in search_paths:
        if not directory.exists():
            continue
        candidate = directory / filename
        if candidate.exists():
            return candidate
    return None

def load_tab_content(filename: str) -> tuple[str | dict, str]:
    """Load tab content from file. Returns (content, file_type)"""
    try:
        tab_file = resolve_tab_file(filename)
        if tab_file is None:
            return f"Tab file '{filename}' not found.", 'error'

        file_ext = tab_file.suffix.lower()
        if file_ext in ['.txt', '.tab']:
            with open(tab_file, 'r', encoding='utf-8') as f:
                return f.read(), 'text'
        if file_ext in ['.pdf', '.png', '.jpg', '.jpeg']:
            return str(tab_file), 'file'
        if file_ext in ['.musicxml', '.xml']:
            return str(tab_file), 'musicxml'
        if file_ext == '.json':
            with open(tab_file, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f), 'json'
                except json.JSONDecodeError as exc:
                    return f"Invalid JSON tab: {exc}", 'error'
        return f"Unsupported file type: {file_ext}", 'error'
    except Exception as e:
        return f"Error loading tab: {e}", 'error'

def sanitize_filename(name: str) -> str:
    """Convert arbitrary text into a filesystem-friendly filename"""
    sanitized = re.sub(r'[^a-zA-Z0-9._-]+', '_', name).strip('_')
    return sanitized or "chart"

def create_musicxml_from_builder(chart_name: str, bpm: int, time_signature: str,
                                 builder_text: str, composer: str = "",
                                 movement_title: str = "",
                                 subtitle: str = "", instrument_label: str = "Guitar",
                                 measure_chords: Dict[int, List[str]] | None = None,
                                 measure_texts: Dict[int, List[str]] | None = None) -> Tuple[bool, str]:
    """Generate a simple MusicXML file from the MVP builder input"""
    try:
        from music21 import chord, clef, duration, expressions, harmony, instrument, meter, metadata, note as m21note, stream, tempo
    except ImportError:
        return False, "music21 is required to generate MusicXML tabs. Please install it and try again."

    lines = []
    for raw_line in builder_text.splitlines():
        stripped = raw_line.strip()
        if stripped and not stripped.startswith('#'):
            lines.append(stripped)

    if not lines:
        return False, "Add at least one measure before generating."

    measure_chords = measure_chords or {}
    measure_texts = measure_texts or {}

    score = stream.Score()
    score.metadata = metadata.Metadata()
    title_text = chart_name.strip() or "Untitled Tab"
    score.metadata.title = title_text

    movement_text = movement_title.strip()
    score.metadata.movementName = movement_text or None

    subtitle_text = subtitle.strip()
    if subtitle_text:
        score.metadata.subtitle = subtitle_text

    composer_text = composer.strip()
    if composer_text:
        score.metadata.composer = composer_text

    part_name = instrument_label.strip() or "Guitar"
    part = stream.Part(id="P1")
    part.partName = part_name
    part.partAbbreviation = (part_name[:3].upper() if len(part_name) > 3 else part_name)
    try:
        inst = instrument.fromString(part_name)
    except Exception:
        inst = instrument.Instrument()
        inst.instrumentName = part_name

    part.insert(0, inst)
    part.insert(0, tempo.MetronomeMark(number=bpm))
    try:
        part.insert(0, meter.TimeSignature(time_signature))
    except Exception:
        part.insert(0, meter.TimeSignature("4/4"))
    part.insert(0, clef.TrebleClef())

    for idx, line in enumerate(lines, start=1):
        measure_stream = stream.Measure(number=idx)
        tokens = [token.strip() for token in line.split() if token.strip()]
        if not tokens:
            continue

        chord_labels = measure_chords.get(idx, [])
        chord_pointer = 0
        current_offset = 0.0
        for token in tokens:
            if ':' not in token:
                return False, f"Line {idx}: '{token}' is missing ':' to separate note and duration."

            symbol, duration_symbol = token.split(':', 1)
            duration_symbol = duration_symbol.lower()
            if duration_symbol not in TAB_DURATION_MAP:
                return False, f"Line {idx}: duration '{duration_symbol}' is not supported."

            quarter_length = TAB_DURATION_MAP[duration_symbol]
            try:
                if symbol.lower() == "rest":
                    element = m21note.Rest()
                else:
                    pitches = [value.strip() for value in symbol.split('+') if value.strip()]
                    if not pitches:
                        return False, f"Line {idx}: '{token}' does not list any notes."
                    if len(pitches) == 1:
                        element = m21note.Note(pitches[0])
                    else:
                        element = chord.Chord(pitches)
            except Exception as exc:
                return False, f"Line {idx}: unable to create note '{symbol}' ({exc})."

            element.duration = duration.Duration(quarter_length)
            measure_stream.append(element)

            if chord_pointer < len(chord_labels):
                label = chord_labels[chord_pointer].strip()
                if label:
                    try:
                        harmony_symbol = harmony.ChordSymbol(label)
                    except Exception:
                        harmony_symbol = expressions.TextExpression(label)
                    harmony_symbol.offset = current_offset
                    harmony_symbol.placement = 'above'
                    measure_stream.insert(harmony_symbol)
                chord_pointer += 1

            current_offset += quarter_length

        if idx in measure_texts:
            for text_label in measure_texts[idx]:
                cue = expressions.TextExpression(text_label)
                cue.placement = 'above'
                measure_stream.insert(0, cue)

        part.append(measure_stream)

    score.append(part)

    try:
        TABS_DIR.mkdir(parents=True, exist_ok=True)
        TABS_MUSICXML_DIR.mkdir(parents=True, exist_ok=True)
        filename = sanitize_filename(chart_name or "chart") + ".musicxml"
        output_path = TABS_MUSICXML_DIR / filename
        score.write('musicxml', fp=str(output_path))
    except Exception as exc:
        return False, f"Could not save MusicXML file: {exc}"

    return True, str(output_path)

JSON_CHORD_SKIP_TOKENS = {
    "riff", "intro", "verse", "chorus", "bridge", "solo", "pre-chorus",
    "hook", "outro", "nc", "n.c.", "repeat", "x2", "x3", "x4", "x5"
}
CHORD_NAME_PATTERN = re.compile(r"^[A-Ga-g][#b]?")

def chord_symbol_to_builder_token(symbol: str) -> str | None:
    """Convert a chord symbol into a builder token like 'C4+E4+G4:q'"""
    cleaned = (symbol or "").strip()
    if not cleaned:
        return None
    lowered = cleaned.lower()
    if lowered in JSON_CHORD_SKIP_TOKENS or lowered.startswith('x'):
        return None
    if lowered in {"n.c", "n.c."}:
        return "rest:q"

    try:
        from music21 import harmony
        chord_symbol = harmony.ChordSymbol(cleaned)
        pitches = []
        for pitch in chord_symbol.pitches:
            octave = pitch.octave if pitch.octave is not None else 4
            pitches.append(f"{pitch.name}{octave}")
        if not pitches:
            match = CHORD_NAME_PATTERN.match(cleaned)
            if match:
                pitches.append(f"{match.group(0).upper()}4")
        if not pitches:
            return None
        return "+".join(pitches) + ":q"
    except Exception:
        match = CHORD_NAME_PATTERN.match(cleaned)
        if not match:
            return None
        root = match.group(0).upper()
        return f"{root}4:q"

def convert_json_tab_to_musicxml(json_path: Path) -> Tuple[bool, str]:
    """Read a legacy JSON tab and convert it into a MusicXML file via the builder"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
    except Exception as exc:
        return False, f"Failed to read {json_path.name}: {exc}"

    tab_data = payload.get('tab') if isinstance(payload, dict) else None
    if not tab_data:
        return False, f"{json_path.name} does not contain a 'tab' object."

    title = tab_data.get('title') or json_path.stem
    artist = tab_data.get('artist_name', '')
    subtitle = tab_data.get('author', '')
    bpm = 110

    builder_lines: List[str] = []
    current_tokens: List[str] = []
    current_chord_labels: List[str] = []
    measure_chords: Dict[int, List[str]] = {}
    measure_texts: Dict[int, List[str]] = {}
    pending_texts: List[str] = []
    measure_counter = 0

    def commit_measure(force: bool = False):
        nonlocal current_tokens, current_chord_labels, pending_texts, measure_counter
        if not current_tokens and not force:
            return
        builder_lines.append(" ".join(current_tokens))
        measure_counter += 1
        if current_chord_labels:
            measure_chords[measure_counter] = current_chord_labels.copy()
        if pending_texts:
            measure_texts.setdefault(measure_counter, []).extend(pending_texts)
            pending_texts = []
        current_tokens = []
        current_chord_labels = []

    for entry in tab_data.get('lines', []):
        entry_type = entry.get('type')
        if entry_type == 'chords':
            for chord_entry in entry.get('chords', []):
                token = chord_symbol_to_builder_token(chord_entry.get('note', ''))
                if not token:
                    continue
                current_tokens.append(token)
                current_chord_labels.append(chord_entry.get('note', '').strip())
                if len(current_tokens) == 4:
                    commit_measure()
            commit_measure()
        elif entry_type == 'lyric':
            lyric_text = entry.get('lyric', '').strip()
            if lyric_text:
                if lyric_text.startswith('[') and lyric_text.endswith(']'):
                    pending_texts.append(lyric_text.strip('[]'))
                else:
                    builder_lines.append(f"# {lyric_text}")
        elif entry_type == 'blank':
            commit_measure(force=False)
        else:
            commit_measure(force=False)

    commit_measure()

    builder_text = "\n".join(builder_lines).strip()
    if not builder_text:
        return False, f"{json_path.name} did not include convertible chord data."

    success, output = create_musicxml_from_builder(
        chart_name=title,
        bpm=bpm,
        time_signature="4/4",
        builder_text=builder_text,
        movement_title=artist,
        subtitle=subtitle,
        instrument_label="Guitar",
        measure_chords=measure_chords,
        measure_texts=measure_texts,
    )
    if success:
        return True, output
    return False, output

def convert_json_tab_file(filename: str) -> Tuple[bool, str]:
    """Helper to convert a JSON tab referenced by filename"""
    json_path = TABS_RAW_JSON_DIR / filename
    if not json_path.exists():
        # Fallback to legacy location for backwards compatibility
        json_path = TABS_DIR / filename
    if not json_path.exists():
        return False, f"{filename} was not found."
    return convert_json_tab_to_musicxml(json_path)

 

def add_new_song(name: str, bpm: int, has_horn: bool = False, has_vocals: bool = False, 
                 energy_level: str = 'standard', is_jam_vehicle: bool = False):
    """Add a new song to the song list"""
    if st.session_state.songs_data is None:
        st.session_state.songs_data = load_song_list()
    
    # Calculate duration
    base_duration = 210  # 3.5 minutes in seconds
    duration_seconds = int(base_duration * (120 / max(bpm, 60)))
    
    st.session_state.songs_data[name] = {
        'bpm': bpm,
        'duration': duration_seconds,
        'has_horn': has_horn,
        'has_vocals': has_vocals,
        'energy_level': energy_level,
        'is_jam_vehicle': is_jam_vehicle,
        'raw_line': f"{name} ({bpm})"
    }
    
    return save_song_list(st.session_state.songs_data)

def update_song(old_name: str, new_name: str, bpm: int, has_horn: bool = False, has_vocals: bool = False,
                energy_level: str = 'standard', is_jam_vehicle: bool = False, artist: str = ''):
    """Update an existing song"""
    if st.session_state.songs_data is None:
        st.session_state.songs_data = load_song_list()
    
    # Remove old entry if name changed
    if old_name != new_name and old_name in st.session_state.songs_data:
        del st.session_state.songs_data[old_name]
    
    # Calculate duration
    base_duration = 210  # 3.5 minutes in seconds
    duration_seconds = int(base_duration * (120 / max(bpm, 60)))
    
    st.session_state.songs_data[new_name] = {
        'bpm': bpm,
        'duration': duration_seconds,
        'has_horn': has_horn,
        'has_vocals': has_vocals,
        'energy_level': energy_level,
        'is_jam_vehicle': is_jam_vehicle,
        'artist': artist,
        'raw_line': f"{new_name} ({bpm})"
    }
    
    return save_song_list(st.session_state.songs_data)

def delete_song(name: str):
    """Delete a song from the song list"""
    if st.session_state.songs_data is None:
        st.session_state.songs_data = load_song_list()
    
    if name in st.session_state.songs_data:
        del st.session_state.songs_data[name]
        return save_song_list(st.session_state.songs_data)
    return False

@st.cache_data
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
        st.error(f"Error loading setlists: {e}")
    
    return sorted(setlists, key=lambda x: x['date'], reverse=True)

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
        st.error(f"Error parsing setlist {file_path}: {e}")
        return None

def format_duration(seconds: int) -> str:
    """Format duration in MM:SS format"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

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
        st.error(f"Error saving setlist: {e}")
        return False

def get_energy_emoji(energy_level: str) -> str:
    """Get emoji for energy level"""
    energy_emojis = {
        'high': '🔥',      # Fire for high energy
        'standard': '',  # Star for standard energy  
        'low': '💤'       # Sleeping for low energy
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

# Main app header
st.markdown("""
<div class="main-header">
    <h1>🎸 Buckingham Conspiracy Hub</h1>
    <p>Setlist Builder • Song Library • Show Archive</p>
</div>
""", unsafe_allow_html=True)

render_control_label("View Mode")
toggle_cols = st.columns(2)
mobile_selected = st.session_state.view_mode == "Mobile"

with toggle_cols[0]:
    if st.button(
        "📱 Mobile View",
        key="view_mode_mobile",
        type="primary" if mobile_selected else "secondary",
        use_container_width=True,
    ):
        st.session_state.view_mode = "Mobile"

with toggle_cols[1]:
    if st.button(
        "🖥️ Desktop View",
        key="view_mode_desktop",
        type="primary" if not mobile_selected else "secondary",
        use_container_width=True,
    ):
        st.session_state.view_mode = "Desktop"

is_mobile_view = st.session_state.view_mode == "Mobile"

# Load data - Initialize if not in session state
if st.session_state.songs_data is None:
    st.session_state.songs_data = load_song_list()

songs_data = st.session_state.songs_data
previous_setlists = load_previous_setlists()

# Create tabs
tab_lyrics, tab_setlist, tab_library, tab_tabs, tab_previous = st.tabs([
    "📜 Lyrics",
    "🎵 Setlist Builder",
    "📚 Song Library",
    "🎸 Tabs",
    "📋 Previous Setlists",
])

with tab_library:
    st.header("📚 Song Library & Editor")
    
    if songs_data:
        # Display song statistics with new metadata
        total_songs = len(songs_data)
        jam_vehicles = len([s for s in songs_data.values() if s.get('is_jam_vehicle')])
        avg_bpm = sum(s['bpm'] for s in songs_data.values()) / len(songs_data)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Songs</div>
                <div class="metric-value">{total_songs}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Jam Vehicles</div>
                <div class="metric-value">{jam_vehicles}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Avg BPM</div>
                <div class="metric-value">{avg_bpm:.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Add new song section
        st.markdown("---")
        with st.expander("➕ Add New Song", expanded=False):
            with st.form("add_song_form"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    new_song_name = st.text_input("Song Name*", placeholder="Enter song name", key="add_song_name")
                    new_song_bpm = st.number_input("BPM*", min_value=60, max_value=200, value=120, key="add_song_bpm")
                
                with col2:
                    new_has_horn = st.checkbox("Has Horn Parts 🎺", key="add_song_horn")
                    new_has_vocals = st.checkbox("Has Vocal Parts 🥁", key="add_song_vocals")
                
                with col3:
                    new_energy_level = styled_selectbox(
                        "Energy Level",
                        get_energy_options(),
                        index=1,
                        key="add_song_energy",
                    )  # Default to 'standard'
                    new_is_jam_vehicle = st.checkbox("Jam Vehicle 🛸", key="add_song_jam")
                
                if st.form_submit_button("➕ Add Song"):
                    if new_song_name.strip():
                        if new_song_name not in songs_data:
                            if add_new_song(new_song_name, new_song_bpm, new_has_horn, new_has_vocals, 
                                          new_energy_level, new_is_jam_vehicle):
                                st.success(f"Added '{new_song_name}' to the song library!")
                                st.rerun()
                            else:
                                st.error("Failed to add song. Please try again.")
                        else:
                            st.error("Song already exists in the library!")
                    else:
                        st.error("Song name is required!")
        
        # Search and filter
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search songs:", placeholder="Enter song name...", key="song_search")
        
        with col2:
            filter_type = styled_selectbox(
                "Filter by",
                [
                    "All Songs",
                    "Horn Songs",
                    "Vocal Songs",
                    "Jam Vehicles",
                    "High Energy",
                    "Standard Energy",
                    "Low Energy",
                ],
                key="song_library_filter",
            )
        
        with col3:
            render_control_label(" ")
            if st.button("🔄 Refresh Library", key="refresh_song_library", use_container_width=True):
                st.session_state.songs_data = load_song_list()
                st.success("Song library refreshed!")
                st.rerun()
        
        # Display songs
        filtered_songs = songs_data
        
        if search_term:
            filtered_songs = {k: v for k, v in songs_data.items() 
                            if search_term.lower() in k.lower()}
        
        if filter_type == "Horn Songs":
            filtered_songs = {k: v for k, v in filtered_songs.items() if v.get('has_horn')}
        elif filter_type == "Vocal Songs":
            filtered_songs = {k: v for k, v in filtered_songs.items() if v.get('has_vocals')}
        elif filter_type == "Jam Vehicles":
            filtered_songs = {k: v for k, v in filtered_songs.items() if v.get('is_jam_vehicle')}
        elif filter_type == "High Energy":
            filtered_songs = {k: v for k, v in filtered_songs.items() if v.get('energy_level') == 'high'}
        elif filter_type == "Standard Energy":
            filtered_songs = {k: v for k, v in filtered_songs.items() if v.get('energy_level') == 'standard'}
        elif filter_type == "Low Energy":
            filtered_songs = {k: v for k, v in filtered_songs.items() if v.get('energy_level') == 'low'}
        
        st.markdown(f"**Showing {len(filtered_songs)} songs**")
        
        # Display songs in a table-like format with edit capabilities
        for song_name, song_info in sorted(filtered_songs.items()):
            # Check if this song is being edited
            is_editing = st.session_state.editing_song == song_name
            
            if is_editing:
                # Edit mode
                st.markdown(f"""
                <div class="edit-song-form">
                    <h4>✏️ Editing: {song_name}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                with st.form(f"edit_song_{song_name}"):
                    # First row: Song name and Artist
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        edited_name = st.text_input("Song Name", value=song_name, key=f"edit_name_{song_name}")
                    with col2:
                        edited_artist = st.text_input("Artist", value=song_info.get('artist', ''), key=f"edit_artist_{song_name}")
                    
                    # Second row: BPM
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        edited_bpm = st.number_input("BPM", min_value=60, max_value=200, value=song_info['bpm'], key=f"edit_bpm_{song_name}")
                    
                    # Third row: Metadata
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        edited_horn = st.checkbox("Horn 🎺", value=song_info.get('has_horn', False), key=f"edit_horn_{song_name}")
                    with col2:
                        edited_vocals = st.checkbox("Vocals 🥁", value=song_info.get('has_vocals', False), key=f"edit_vocals_{song_name}")
                    with col3:
                        current_energy = song_info.get('energy_level', 'standard')
                        energy_index = get_energy_options().index(current_energy) if current_energy in get_energy_options() else 1
                        edited_energy = styled_selectbox(
                            "Energy",
                            get_energy_options(),
                            index=energy_index,
                            key=f"edit_energy_{song_name}",
                        )
                    with col4:
                        edited_jam = st.checkbox("Jam Vehicle 🎸", value=song_info.get('is_jam_vehicle', False), key=f"edit_jam_{song_name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes"):
                            if edited_name.strip():
                                if update_song(song_name, edited_name, edited_bpm, edited_horn, edited_vocals, 
                                              edited_energy, edited_jam, edited_artist):
                                    st.session_state.editing_song = None
                                    st.success(f"Updated '{edited_name}'!")
                                    st.rerun()
                                else:
                                    st.error("Failed to update song.")
                            else:
                                st.error("Song name cannot be empty!")
                    
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.editing_song = None
                            st.rerun()
            else:
                # Display mode
                col1, col2, col3, col4, col5, col6 = st.columns([2.5, 1.5, 1, 1, 1, 1])
                
                with col1:
                    markers = ""
                    if song_info.get('has_horn'):
                        markers += "🎺 "
                    if song_info.get('has_vocals'):
                        markers += "🥁 "
                    if song_info.get('is_jam_vehicle'):
                        markers += "🛸"
                    
                    energy_emoji = get_energy_emoji(song_info.get('energy_level', 'standard'))
                    st.markdown(f"{energy_emoji} **{song_name}** {markers}")
                
                with col2:
                    artist = song_info.get('artist', '')
                    st.markdown(f"*{artist if artist else '—'}*")
                
                with col3:
                    st.markdown(f"**{song_info['bpm']}** BPM")
                
                with col4:
                    st.markdown(f"**{format_duration(song_info['duration'])}**")
                
                with col5:
                    if st.button(f"✏️", key=f"edit_btn_{song_name}", help="Edit song"):
                        st.session_state.editing_song = song_name
                        st.rerun()
                
                with col6:
                    if st.button(f"🗑️", key=f"delete_btn_{song_name}", help="Delete song"):
                        if delete_song(song_name):
                            st.success(f"Deleted '{song_name}'!")
                            st.rerun()
                        else:
                            st.error("Failed to delete song.")
    else:
        st.error("No songs found. Please check the song list file.")

with tab_setlist:
    st.header("🎵 Setlist Builder")
    
    # Setlist metadata
    if is_mobile_view:
        venue = st.text_input("Venue", value=st.session_state.setlist_metadata['venue'], key="setlist_venue")
        st.session_state.setlist_metadata['venue'] = venue

        date = st.text_input("Date (MM/DD/YY)", value=st.session_state.setlist_metadata['date'], key="setlist_date")
        st.session_state.setlist_metadata['date'] = date
    else:
        col1, col2 = st.columns(2)
        with col1:
            venue = st.text_input("Venue", value=st.session_state.setlist_metadata['venue'], key="setlist_venue")
            st.session_state.setlist_metadata['venue'] = venue

        with col2:
            date = st.text_input("Date (MM/DD/YY)", value=st.session_state.setlist_metadata['date'], key="setlist_date")
            st.session_state.setlist_metadata['date'] = date
    
    # Set break durations
    if is_mobile_view:
        set1_break = st.number_input("Set 1 Break (minutes)", value=15, min_value=0, max_value=60, key="set1_break")
        st.session_state.setlist_metadata['set_breaks']['set1_break'] = set1_break

        set2_break = st.number_input("Set 2 Break (minutes)", value=15, min_value=0, max_value=60, key="set2_break")
        st.session_state.setlist_metadata['set_breaks']['set2_break'] = set2_break
    else:
        col1, col2 = st.columns(2)
        with col1:
            set1_break = st.number_input("Set 1 Break (minutes)", value=15, min_value=0, max_value=60, key="set1_break")
            st.session_state.setlist_metadata['set_breaks']['set1_break'] = set1_break

        with col2:
            set2_break = st.number_input("Set 2 Break (minutes)", value=15, min_value=0, max_value=60, key="set2_break")
            st.session_state.setlist_metadata['set_breaks']['set2_break'] = set2_break
    
    # Song selector
    st.subheader("Add Songs to Sets")
    
    if is_mobile_view:
        song_names = list(songs_data.keys())
        selected_song = styled_selectbox(
            "Select a song to add",
            [""] + sorted(song_names),
            key="song_selector",
        )

        target_set = styled_selectbox(
            "Add to set",
            ["Set 1", "Set 2", "Set 3"],
            key="target_set",
        )
    else:
        col1, col2 = st.columns([2, 1])
        with col1:
            # Create searchable song list
            song_names = list(songs_data.keys())
            selected_song = styled_selectbox(
                "Select a song to add",
                [""] + sorted(song_names),
                key="song_selector",
            )

        with col2:
            target_set = styled_selectbox(
                "Add to set",
                ["Set 1", "Set 2", "Set 3"],
                key="target_set",
            )
    
    # Add song button
    if st.button("➕ Add Song", key="add_song_to_setlist", use_container_width=is_mobile_view) and selected_song:
        set_key = f"set{target_set.split()[-1]}"
        if selected_song not in st.session_state.current_setlist[set_key]:
            st.session_state.current_setlist[set_key].append(selected_song)
            st.success(f"Added '{selected_song}' to {target_set}")
            st.rerun()
    
    # Display current setlist
    st.markdown("---")
    
    # Calculate timing for each set
    set1_duration, set1_with_break = calculate_set_timing(
        st.session_state.current_setlist['set1'], 
        songs_data, 
        st.session_state.setlist_metadata['set_breaks']['set1_break']
    )
    set2_duration, set2_with_break = calculate_set_timing(
        st.session_state.current_setlist['set2'], 
        songs_data, 
        st.session_state.setlist_metadata['set_breaks']['set2_break']
    )
    set3_duration, set3_with_break = calculate_set_timing(
        st.session_state.current_setlist['set3'], 
        songs_data
    )
    
    total_show_time = set1_duration + set2_duration + set3_duration + \
                     (st.session_state.setlist_metadata['set_breaks']['set1_break'] * 60) + \
                     (st.session_state.setlist_metadata['set_breaks']['set2_break'] * 60)
    
    # Summary metrics
    if is_mobile_view:
        row1_col1, row1_col2 = st.columns(2)

        with row1_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Set 1 Length</div>
                <div class="metric-value">{format_duration(set1_duration)}</div>
            </div>
            """, unsafe_allow_html=True)

        with row1_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Set 2 Length</div>
                <div class="metric-value">{format_duration(set2_duration)}</div>
            </div>
            """, unsafe_allow_html=True)

        row2_col1, row2_col2 = st.columns(2)

        with row2_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Set 3 Length</div>
                <div class="metric-value">{format_duration(set3_duration)}</div>
            </div>
            """, unsafe_allow_html=True)

        with row2_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Show</div>
                <div class="metric-value">{format_duration(total_show_time)}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Set 1 Length</div>
                <div class="metric-value">{format_duration(set1_duration)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Set 2 Length</div>
                <div class="metric-value">{format_duration(set2_duration)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Set 3 Length</div>
                <div class="metric-value">{format_duration(set3_duration)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Show</div>
                <div class="metric-value">{format_duration(total_show_time)}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Display sets
    for set_num, set_name in [(1, "Set 1"), (2, "Set 2"), (3, "Set 3")]:
        set_key = f"set{set_num}"
        
        with st.expander(f"🎵 {set_name} ({len(st.session_state.current_setlist[set_key])} songs)", expanded=True):
            if st.session_state.current_setlist[set_key]:
                for i, song in enumerate(st.session_state.current_setlist[set_key]):
                    song_info = songs_data.get(song, {})
                    markers = ""
                    if song_info.get('has_horn'):
                        markers += "🎺 "
                    if song_info.get('has_vocals'):
                        markers += "🥁 "

                    if is_mobile_view:
                        st.markdown(f"""
                        <div class="song-card">
                            <strong>{song}</strong> {markers}<br>
                            <small>BPM: {song_info.get('bpm', 'Unknown')} | Duration: {format_duration(song_info.get('duration', 210))}</small>
                        </div>
                        """, unsafe_allow_html=True)

                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        with btn_col1:
                            if st.button("⬆️", key=f"up_{set_key}_{i}", disabled=i==0, use_container_width=True):
                                # Move song up
                                songs = st.session_state.current_setlist[set_key]
                                songs[i], songs[i-1] = songs[i-1], songs[i]
                                st.rerun()

                        with btn_col2:
                            if st.button(
                                "⬇️",
                                key=f"down_{set_key}_{i}",
                                disabled=i==len(st.session_state.current_setlist[set_key])-1,
                                use_container_width=True,
                            ):
                                # Move song down
                                songs = st.session_state.current_setlist[set_key]
                                songs[i], songs[i+1] = songs[i+1], songs[i]
                                st.rerun()

                        with btn_col3:
                            if st.button("🗑️", key=f"remove_{set_key}_{i}", use_container_width=True):
                                # Remove song
                                st.session_state.current_setlist[set_key].pop(i)
                                st.rerun()
                    else:
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                        with col1:
                            st.markdown(f"""
                            <div class="song-card">
                                <strong>{song}</strong> {markers}<br>
                                <small>BPM: {song_info.get('bpm', 'Unknown')} | Duration: {format_duration(song_info.get('duration', 210))}</small>
                            </div>
                            """, unsafe_allow_html=True)

                        with col2:
                            if st.button("⬆️", key=f"up_{set_key}_{i}", disabled=i==0):
                                # Move song up
                                songs = st.session_state.current_setlist[set_key]
                                songs[i], songs[i-1] = songs[i-1], songs[i]
                                st.rerun()

                        with col3:
                            if st.button("⬇️", key=f"down_{set_key}_{i}", disabled=i==len(st.session_state.current_setlist[set_key])-1):
                                # Move song down
                                songs = st.session_state.current_setlist[set_key]
                                songs[i], songs[i+1] = songs[i+1], songs[i]
                                st.rerun()

                        with col4:
                            if st.button("🗑️", key=f"remove_{set_key}_{i}"):
                                # Remove song
                                st.session_state.current_setlist[set_key].pop(i)
                                st.rerun()
            else:
                st.markdown(
                    f"""
                    <div class="inline-hint">
                        <span>👆</span>
                        <p>No songs in {set_name} yet. Add some songs above!</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    
    # Export functionality
    st.markdown("---")
    if is_mobile_view:
        if st.button("📄 Export Setlist", key="export_setlist", use_container_width=True):
            # Create export data
            export_data = {
                'venue': venue,
                'date': date,
                'setlist': st.session_state.current_setlist,
                'timing': {
                    'set1_duration': format_duration(set1_duration),
                    'set2_duration': format_duration(set2_duration),
                    'set3_duration': format_duration(set3_duration),
                    'total_show': format_duration(total_show_time)
                }
            }

            st.download_button(
                "💾 Download JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"setlist_{venue}_{date.replace('/', '')}.json",
                mime="application/json",
                use_container_width=True,
            )

        if st.button("🗑️ Clear All Sets", use_container_width=True):
            st.session_state.current_setlist = {'set1': [], 'set2': [], 'set3': []}
            st.success("All sets cleared!")
            st.rerun()
    else:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📄 Export Setlist", key="export_setlist"):
                # Create export data
                export_data = {
                    'venue': venue,
                    'date': date,
                    'setlist': st.session_state.current_setlist,
                    'timing': {
                        'set1_duration': format_duration(set1_duration),
                        'set2_duration': format_duration(set2_duration),
                        'set3_duration': format_duration(set3_duration),
                        'total_show': format_duration(total_show_time)
                    }
                }

                st.download_button(
                    "💾 Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"setlist_{venue}_{date.replace('/', '')}.json",
                    mime="application/json"
                )

        with col2:
            if st.button("🗑️ Clear All Sets"):
                st.session_state.current_setlist = {'set1': [], 'set2': [], 'set3': []}
                st.success("All sets cleared!")
                st.rerun()

with tab_previous:
    st.header("📋 Previous Setlists")
    
    if previous_setlists:
        # Display filters
        venues = sorted(list(set(setlist['venue'] for setlist in previous_setlists)))
        selected_venue = styled_selectbox(
            "Filter by venue",
            ["All Venues"] + venues,
            key="previous_setlists_venue_filter",
        )
        
        # Filter setlists
        filtered_setlists = previous_setlists
        if selected_venue != "All Venues":
            filtered_setlists = [s for s in previous_setlists if s['venue'] == selected_venue]
        
        st.markdown(f"**Showing {len(filtered_setlists)} setlists**")
        
        for i, setlist in enumerate(filtered_setlists):
            setlist_id = f"{setlist['venue']}_{setlist['date']}"
            is_editing = st.session_state.editing_setlist == setlist_id
            
            if is_editing:
                # Edit mode
                st.markdown(f"""
                <div class="edit-song-form">
                    <h4>✏️ Editing: {setlist['venue']} - {setlist['date']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Load setlist data into session state if not already there
                if st.session_state.edited_setlist_data is None:
                    st.session_state.edited_setlist_data = setlist.copy()
                
                # Venue and date editing (outside form for better UX)
                if is_mobile_view:
                    edited_venue = st.text_input(
                        "Venue",
                        value=st.session_state.edited_setlist_data['venue'],
                        key=f"venue_{setlist_id}",
                    )
                    st.session_state.edited_setlist_data['venue'] = edited_venue

                    edited_date = st.text_input(
                        "Date",
                        value=st.session_state.edited_setlist_data['date'],
                        key=f"date_{setlist_id}",
                    )
                    st.session_state.edited_setlist_data['date'] = edited_date
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        edited_venue = st.text_input(
                            "Venue",
                            value=st.session_state.edited_setlist_data['venue'],
                            key=f"venue_{setlist_id}",
                        )
                        st.session_state.edited_setlist_data['venue'] = edited_venue
                    with col2:
                        edited_date = st.text_input(
                            "Date",
                            value=st.session_state.edited_setlist_data['date'],
                            key=f"date_{setlist_id}",
                        )
                        st.session_state.edited_setlist_data['date'] = edited_date
                
                # Edit sets
                st.subheader("Edit Sets")
                if is_mobile_view:
                    set_columns = [st.container(), st.container(), st.container()]
                else:
                    set_columns = st.columns(3)

                for set_num, (col, set_name) in enumerate(zip(set_columns, ["Set 1", "Set 2", "Set 3"]), 1):
                    set_key = f"set{set_num}"
                    set_songs = st.session_state.edited_setlist_data['sets'].get(set_key, [])
                    
                    with col:
                        st.markdown(f"**{set_name}**")
                        
                        # Add song to set
                        song_names = list(songs_data.keys()) if songs_data else []
                        if is_mobile_view:
                            add_song_col1 = st.container()
                            add_song_col2 = st.container()
                        else:
                            add_song_col1, add_song_col2 = st.columns([3, 1])

                        with add_song_col1:
                            new_song = styled_selectbox(
                                f"Add song to {set_name}",
                                [""] + sorted(song_names),
                                key=f"add_song_{set_key}_{setlist_id}",
                            )
                        with add_song_col2:
                            if st.button(
                                "➕",
                                key=f"add_btn_{set_key}_{setlist_id}",
                                help=f"Add to {set_name}",
                                use_container_width=is_mobile_view,
                            ):
                                if new_song and new_song not in [s['name'] for s in set_songs]:
                                    song_info = songs_data.get(new_song, {})
                                    set_songs.append({
                                        'name': new_song,
                                        'bpm': song_info.get('bpm'),
                                        'raw_line': f"{new_song} ({song_info.get('bpm', '')})" if song_info.get('bpm') else new_song
                                    })
                                    st.rerun()
                        
                        st.markdown("---")
                        
                        # Display and edit existing songs
                        for j, song in enumerate(set_songs):
                            if is_mobile_view:
                                st.markdown(f"• {song['name']} ({song['bpm']})" if song['bpm'] else f"• {song['name']}")
                                action_col1, action_col2 = st.columns(2)
                                with action_col1:
                                    if st.button(
                                        "⬆️",
                                        key=f"up_{set_key}_{j}_{setlist_id}",
                                        disabled=j==0,
                                        help="Move up",
                                        use_container_width=True,
                                    ):
                                        set_songs[j], set_songs[j-1] = set_songs[j-1], set_songs[j]
                                        st.rerun()

                                with action_col2:
                                    if st.button(
                                        "🗑️",
                                        key=f"del_{set_key}_{j}_{setlist_id}",
                                        help="Delete",
                                        use_container_width=True,
                                    ):
                                        set_songs.pop(j)
                                        st.rerun()
                            else:
                                song_col1, song_col2, song_col3 = st.columns([3, 1, 1])

                                with song_col1:
                                    st.markdown(f"• {song['name']} ({song['bpm']})" if song['bpm'] else f"• {song['name']}")

                                with song_col2:
                                    if st.button("⬆️", key=f"up_{set_key}_{j}_{setlist_id}", disabled=j==0, help="Move up"):
                                        set_songs[j], set_songs[j-1] = set_songs[j-1], set_songs[j]
                                        st.rerun()

                                with song_col3:
                                    if st.button("🗑️", key=f"del_{set_key}_{j}_{setlist_id}", help="Delete"):
                                        set_songs.pop(j)
                                        st.rerun()
                
                # Save/Cancel buttons
                st.markdown("---")
                if is_mobile_view:
                    if st.button("💾 Save Setlist", key=f"save_{setlist_id}", type="primary", use_container_width=True):
                        # Save to file
                        if save_setlist_to_file(st.session_state.edited_setlist_data):
                            st.session_state.editing_setlist = None
                            st.session_state.edited_setlist_data = None
                            # Clear cache to reload data
                            st.cache_data.clear()
                            st.success(f"Saved changes to '{edited_venue} - {edited_date}'!")
                            st.rerun()
                        else:
                            st.error("Failed to save setlist changes.")

                    if st.button("❌ Cancel", key=f"cancel_{setlist_id}", use_container_width=True):
                        st.session_state.editing_setlist = None
                        st.session_state.edited_setlist_data = None
                        st.rerun()
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Save Setlist", key=f"save_{setlist_id}", type="primary"):
                            # Save to file
                            if save_setlist_to_file(st.session_state.edited_setlist_data):
                                st.session_state.editing_setlist = None
                                st.session_state.edited_setlist_data = None
                                # Clear cache to reload data
                                st.cache_data.clear()
                                st.success(f"Saved changes to '{edited_venue} - {edited_date}'!")
                                st.rerun()
                            else:
                                st.error("Failed to save setlist changes.")

                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_{setlist_id}"):
                            st.session_state.editing_setlist = None
                            st.session_state.edited_setlist_data = None
                            st.rerun()
            
            else:
                # Display mode
                with st.expander(f"🎸 {setlist['venue']} - {setlist['date']}", expanded=False):
                    # Edit button
                    if st.button(
                        f"✏️ Edit Setlist",
                        key=f"edit_setlist_{setlist_id}",
                        use_container_width=is_mobile_view,
                    ):
                        st.session_state.editing_setlist = setlist_id
                        st.session_state.edited_setlist_data = None  # Will be loaded in edit mode
                        st.rerun()
                    
                    if is_mobile_view:
                        display_columns = [st.container(), st.container(), st.container()]
                    else:
                        display_columns = st.columns(3)

                    for set_num, (col, set_name) in enumerate(zip(display_columns, ["Set 1", "Set 2", "Set 3"]), 1):
                        set_key = f"set{set_num}"
                        set_songs = setlist['sets'].get(set_key, [])
                        
                        with col:
                            st.markdown(f"**{set_name}**")
                            if set_songs:
                                for song in set_songs:
                                    song_name = song['name']
                                    bpm_text = f" ({song['bpm']})" if song['bpm'] else ""
                                    st.markdown(f"• {song_name}{bpm_text}")
                            else:
                                st.markdown("*No songs*")
    else:
        st.info("No previous setlists found.")

with tab_lyrics:
    st.header("📜 Lyrics Viewer")
    
    render_control_label("Select a song to view lyrics")
    available_lyrics = load_available_lyrics()

    song_index = 0
    if (
        st.session_state.selected_lyrics_song
        and st.session_state.selected_lyrics_song in available_lyrics
    ):
        song_index = available_lyrics.index(st.session_state.selected_lyrics_song) + 1

    if is_mobile_view:
        selected_song = styled_selectbox(
            "Choose a song",
            [""] + available_lyrics,
            index=song_index,
            key="lyrics_song_selector",
        )
        if selected_song:
            st.session_state.selected_lyrics_song = selected_song

        if st.button("🔄 Refresh Lyrics", key="refresh_lyrics", use_container_width=True):
            st.rerun()

        if selected_song:
            toggle_label = "↩️ Exit Full Screen" if st.session_state.lyrics_fullscreen else "🔍 Full Screen"
            if st.button(toggle_label, key="lyrics_fullscreen_toggle", use_container_width=True):
                st.session_state.lyrics_fullscreen = not st.session_state.lyrics_fullscreen
    else:
        selector_cols = st.columns([3, 1, 1])
        with selector_cols[0]:
            selected_song = styled_selectbox(
                "Choose a song",
                [""] + available_lyrics,
                index=song_index,
                key="lyrics_song_selector",
            )
            if selected_song:
                st.session_state.selected_lyrics_song = selected_song

        with selector_cols[1]:
            st.markdown("<p class='control-label'>&nbsp;</p>", unsafe_allow_html=True)
            if st.button("🔄 Refresh Lyrics", key="refresh_lyrics", use_container_width=True):
                st.rerun()

        with selector_cols[2]:
            st.markdown("<p class='control-label'>&nbsp;</p>", unsafe_allow_html=True)
            if selected_song:
                toggle_label = "↩️ Exit Full Screen" if st.session_state.lyrics_fullscreen else "🔍 Full Screen"
                if st.button(toggle_label, key="lyrics_fullscreen_toggle", use_container_width=True):
                    st.session_state.lyrics_fullscreen = not st.session_state.lyrics_fullscreen

    if not selected_song and st.session_state.lyrics_fullscreen:
        st.session_state.lyrics_fullscreen = False

    if available_lyrics:
        
        # Display lyrics
        if selected_song:
            lyrics_content = load_lyrics_content(selected_song)
            formatted_lyrics = format_lyrics_for_display(lyrics_content)
            
            # Get artist info if available
            artist_info = ""
            if songs_data and selected_song in songs_data:
                artist = songs_data[selected_song].get('artist', '')
                artist_info = f"<div style='text-align: center; color: #ccc; font-size: 16px; margin-bottom: 1rem;'>{artist}</div>" if artist else ""
            
            # Determine styling based on view mode
            device_type = st.session_state.view_mode
            if device_type == "Mobile":
                base_container = "lyrics-container-mobile"
                text_class = "lyrics-text-mobile"
            else:  # Desktop
                base_container = "lyrics-container"
                text_class = "lyrics-text-desktop"

            fullscreen_class = "lyrics-container-fullscreen" if st.session_state.lyrics_fullscreen else ""
            container_class = f"{base_container} {fullscreen_class}".strip()
            
            # Display the lyrics with device-specific styling
            st.markdown(f"""
            <div class="{container_class}">
                <div class="lyrics-title">{selected_song}</div>
                {artist_info}
                <div class="{text_class}" style="white-space: normal;">{formatted_lyrics}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if not st.session_state.lyrics_fullscreen:
                # Add helpful info
                st.markdown("---")
                if is_mobile_view:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Display Mode</div>
                        <div class="metric-value">{device_type}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    line_count = len(lyrics_content.split('\n'))
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Lines</div>
                        <div class="metric-value">{line_count}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Available Songs</div>
                        <div class="metric-value">{len(available_lyrics)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">Display Mode</div>
                            <div class="metric-value">{device_type}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        line_count = len(lyrics_content.split('\n'))
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">Lines</div>
                            <div class="metric-value">{line_count}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-title">Available Songs</div>
                            <div class="metric-value">{len(available_lyrics)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Tips section
                with st.expander("💡 Lyrics Viewer Tips"):
                    st.markdown("""
                    - **Mobile Mode**: Optimized for phones with larger text and tighter spacing
                    - **Desktop Mode**: Balanced view for laptop/desktop screens
                    - Scroll within the lyrics box to navigate through the song
                    - The lyrics are loaded from `.txt` files in the `song_data` directory
                    - To add new lyrics, create a `.txt` file with the song name in the `song_data` folder
                    """)
        else:
            st.markdown(
                """
                <div class="inline-hint">
                    <span>👆</span>
                    <p>Select a song from the dropdown above to view its lyrics.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:
        st.warning("No lyrics files found in the song_data directory.")
        st.markdown("""
        **To add lyrics:**
        1. Create a `.txt` file in the `buckingham_conspiracy/song_data/` directory
        2. Name the file with the song name (e.g., `Move.txt`)
        3. Add the lyrics to the file, one line at a time
        4. Refresh this page to see the new lyrics appear
        """)

with tab_tabs:
    st.header("🎸 Tabs & Notation")
    st.markdown("### 🎧 Browse Saved Files")

    if is_mobile_view:
        st.markdown("**Select a tab file to view:**")
        if st.button("🔄 Refresh Tabs", key="refresh_tabs", use_container_width=True):
            st.rerun()
    else:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**Select a tab file to view:**")
        with col2:
            if st.button("🔄 Refresh Tabs", key="refresh_tabs"):
                st.rerun()

    if 'pending_tab_selection' in st.session_state:
        st.session_state.tabs_file_selector = st.session_state.pop('pending_tab_selection')

    # Load available tabs
    available_tabs = load_available_tabs()
    
    if available_tabs:
        # File selector
        selected_tab = styled_selectbox(
            "Choose a tab file",
            [""] + available_tabs,
            key="tabs_file_selector",
        )
        
        # Display tabs
        if selected_tab:
            tab_content, file_type = load_tab_content(selected_tab)
            
            if file_type == 'text':
                # Display ASCII tabs
                tab_container_class = "lyrics-container-mobile" if is_mobile_view else "lyrics-container"
                tab_text_class = "lyrics-text-mobile" if is_mobile_view else "lyrics-text-desktop"
                st.markdown(f"""
                <div class="{tab_container_class}">
                    <div class="lyrics-title">{selected_tab}</div>
                    <div class="{tab_text_class}">{tab_content}</div>
                </div>
                """, unsafe_allow_html=True)
            
            elif file_type == 'musicxml':
                st.subheader(selected_tab)
                viewer_result = musicxml_viewer(tab_content, key=f"musicxml_{selected_tab}")
                if isinstance(viewer_result, str) and viewer_result.startswith("Error"):
                    st.error(viewer_result)
            elif file_type == 'json':
                st.subheader(selected_tab)
                tab_payload = tab_content if isinstance(tab_content, dict) else {}
                tab_meta = tab_payload.get('tab', {}) if isinstance(tab_payload, dict) else {}

                meta_pairs = [
                    ('Song Title', tab_meta.get('title', 'Unknown')),
                    ('Artist', tab_meta.get('artist_name', 'Unknown')),
                    ('Tuning', tab_meta.get('tuning', 'Standard') or 'Standard'),
                ]
                if is_mobile_view:
                    for label, value in meta_pairs:
                        st.markdown(
                            f"""
                            <div class="metric-card">
                                <div class="metric-title">{label}</div>
                                <div class="metric-value">{value}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    col_a, col_b, col_c = st.columns(3)
                    for column, (label, value) in zip((col_a, col_b, col_c), meta_pairs):
                        with column:
                            st.markdown(
                                f"""
                                <div class="metric-card">
                                    <div class="metric-title">{label}</div>
                                    <div class="metric-value">{value}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                line_count = len(tab_meta.get('lines', [])) if isinstance(tab_meta, dict) else 0
                st.markdown(
                    f"This JSON tab contains **{line_count}** structured lines parsed from Ultimate Guitar."
                )

                with st.expander("Raw Tab Payload", expanded=False):
                    st.json(tab_content)
            elif file_type == 'file':
                # Display file (PDF, image, etc.)
                st.subheader(selected_tab)
                file_ext = Path(selected_tab).suffix.lower()
                
                if file_ext == '.pdf':
                    with open(tab_content, 'rb') as f:
                        st.download_button(
                            label="📥 Download PDF",
                            data=f,
                            file_name=selected_tab,
                            mime="application/pdf",
                            use_container_width=is_mobile_view,
                        )
                    st.info("PDF files can be downloaded. Future updates may include in-browser viewing.")
                
                elif file_ext in ['.png', '.jpg', '.jpeg']:
                    st.image(tab_content, use_container_width=True)
            
            else:  # error
                st.error(tab_content)
            
            # Add helpful info
            st.markdown("---")
            file_ext = Path(selected_tab).suffix.upper()[1:] if Path(selected_tab).suffix else "Unknown"
            tab_path = resolve_tab_file(selected_tab)
            file_size = tab_path.stat().st_size if tab_path and tab_path.exists() else 0
            size_kb = file_size / 1024

            if is_mobile_view:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">File Type</div>
                    <div class="metric-value">{file_ext}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">File Size</div>
                    <div class="metric-value">{size_kb:.1f} KB</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Available Tabs</div>
                    <div class="metric-value">{len(available_tabs)}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">File Type</div>
                        <div class="metric-value">{file_ext}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">File Size</div>
                        <div class="metric-value">{size_kb:.1f} KB</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Available Tabs</div>
                        <div class="metric-value">{len(available_tabs)}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Tips section
            with st.expander("💡 Tabs Viewer Tips"):
                st.markdown("""
                - **ASCII Tabs** (`.txt`, `.tab`): Displayed directly in the browser
                - **PDF Files**: Available for download, optimized for printing
                - **Images** (`.png`, `.jpg`): Guitar tablature or sheet music images
                                        - **JSON Tabs** (`.json`): Structured payloads fetched from Ultimate Guitar
                - Files are loaded from the `song_data/tabs/` directory
                - To add new tabs:
                  1. Save your tab file in `buckingham_conspiracy/song_data/tabs/`
                                            2. Supported formats: `.txt`, `.tab`, `.json`, `.pdf`, `.png`, `.jpg`
                  3. Name the file with the song name for easy reference
                  4. Refresh this page to see the new tabs appear
                """)
        else:
            st.markdown(
                """
                <div class="inline-hint">
                    <span>👆</span>
                    <p>Select a tab file from the dropdown above to view it.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    else:
        st.warning("No tab files found in the song_data/tabs directory.")
        st.markdown("""
        **To add tabs:**
        1. Create or save your tab file in the `buckingham_conspiracy/song_data/tabs/` directory
        2. Supported formats: `.txt` (ASCII tabs), `.tab`, `.pdf`, `.png`, `.jpg`
        3. Name the file with the song name (e.g., `Move.txt`, `Superstition.pdf`)
        4. Refresh this page to see the new tabs appear
        """)

    st.markdown("---")
    with st.expander("🛠️ Quick Tab Builder (MVP)", expanded=False):
        st.markdown(
            "Build a simple riff directly in the Hub and save it as a MusicXML chart. "
            "Use space-separated tokens with the `NOTE:DURATION` format (ex: `C4:q`). "
            "Write each measure on its own line; prefix lines with `#` to add comments."
        )

        with st.form("tab_builder_form"):
            builder_chart_name = st.text_input("Chart Name", placeholder="e.g., Late Night Groove", key="tab_builder_chart_name")
            builder_artist_name = st.text_input("Artist / Movement Title", value="Buckingham Conspiracy", key="tab_builder_artist")
            builder_subtitle = st.text_input("Subtitle (optional)", placeholder="e.g., Verse idea", key="tab_builder_subtitle")
            if is_mobile_view:
                builder_col1 = st.container()
                builder_col2 = st.container()
                builder_col3 = st.container()
            else:
                builder_col1, builder_col2, builder_col3 = st.columns(3)
            with builder_col1:
                builder_bpm = st.number_input("Tempo (BPM)", min_value=40, max_value=240, value=120, key="tab_builder_bpm")
            with builder_col2:
                builder_time_signature = styled_selectbox(
                    "Time Signature",
                    ["4/4", "3/4", "6/8"],
                    index=0,
                    key="tab_builder_time_signature",
                )
            with builder_col3:
                builder_instrument_label = st.text_input("Instrument Label", value="Guitar", key="tab_builder_instrument_label")
            builder_measure_input = st.text_area(
                "Measure Input",
                height=180,
                key="tab_builder_measure_input",
                help="Example: C4:q E4:q G4:q C5:q",
            )
            st.markdown("<p style='color: var(--text-primary); font-size: 0.95rem;'>Supported durations: w (whole), h (half), q (quarter), e (eighth), s (sixteenth). Use <code>rest:q</code> for rests.</p>", unsafe_allow_html=True)
            auto_preview = st.checkbox("Auto-preview after saving", value=True, key="tab_builder_auto_preview")
            builder_submitted = st.form_submit_button("Generate MusicXML")

        if builder_submitted:
            builder_text = (builder_measure_input or "").strip()
            chart_label = builder_chart_name.strip()

            if not chart_label:
                st.error("Chart name is required.")
            elif not builder_text:
                st.error("Enter at least one measure before generating.")
            else:
                success, result = create_musicxml_from_builder(
                    chart_label,
                    int(builder_bpm),
                    builder_time_signature,
                    builder_text,
                    movement_title=builder_artist_name,
                    subtitle=builder_subtitle,
                    instrument_label=builder_instrument_label,
                )
                if success:
                    generated_path = Path(result)
                    st.success(f"Saved {generated_path.name} to song_data/tabs")
                    if auto_preview:
                        st.session_state.tabs_file_selector = generated_path.name
                    st.rerun()
                else:
                    st.error(result)

    st.markdown("---")
    with st.expander("♻️ Convert Legacy JSON Tabs", expanded=False):
        if TABS_RAW_JSON_DIR.exists():
            json_tab_files = sorted([f.name for f in TABS_RAW_JSON_DIR.glob("*.json")])
        else:
            json_tab_files = []
        if json_tab_files:
            st.caption("Pick any of the legacy Ultimate-Guitar exports and convert them into MusicXML charts for the viewer.")
            selected_json_tabs = st.multiselect(
                "Select JSON tabs to convert:",
                options=json_tab_files,
                key="json_tab_multiselect"
            )
            if is_mobile_view:
                convert_selected = st.button("Convert Selected", key="convert_selected_json", use_container_width=True)
                convert_all = st.button("Convert All JSON", key="convert_all_json", use_container_width=True)
            else:
                col_conv1, col_conv2 = st.columns(2)
                with col_conv1:
                    convert_selected = st.button("Convert Selected", key="convert_selected_json")
                with col_conv2:
                    convert_all = st.button("Convert All JSON", key="convert_all_json")

            conversion_triggered = convert_selected or convert_all
            if conversion_triggered:
                targets = json_tab_files if convert_all else selected_json_tabs
                if not targets:
                    st.warning("Select at least one JSON file to convert.")
                else:
                    conversion_messages = []
                    last_successful = None
                    for filename in targets:
                        success, message = convert_json_tab_file(filename)
                        if success:
                            conversion_messages.append(f"✅ {Path(message).name} created")
                            last_successful = Path(message).name
                        else:
                            conversion_messages.append(f"❌ {filename}: {message}")
                    for msg in conversion_messages:
                        st.write(msg)
                    if last_successful:
                        st.session_state.pending_tab_selection = last_successful
                        st.rerun()
        else:
            st.info("No legacy JSON tabs detected in song_data/tabs/raw_json.")

# Sidebar with quick stats
st.sidebar.markdown("### 🎸 Quick Stats")
if st.session_state.current_setlist:
    total_songs_in_setlist = sum(len(songs) for songs in st.session_state.current_setlist.values())
    st.sidebar.metric("Songs in Current Setlist", total_songs_in_setlist)

st.sidebar.metric("Total Songs in Library", len(st.session_state.songs_data) if st.session_state.songs_data else 0)
st.sidebar.metric("Previous Setlists", len(previous_setlists))
st.sidebar.metric("Lyrics Available", len(load_available_lyrics()))
st.sidebar.metric("Tabs Available", len(load_available_tabs()))

st.sidebar.markdown("---")
st.sidebar.markdown("### Legend")
st.sidebar.markdown("🎺 = Horn parts")
st.sidebar.markdown("🥁 = Drum Vocal parts")
st.sidebar.markdown("🛸 = Jam vehicle")
st.sidebar.markdown("🔥 = High energy")
st.sidebar.markdown("💤 = Low energy")
