import streamlit as st
import os
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path

# Get the base directory (parent of src/)
BASE_DIR = Path(__file__).resolve().parent.parent
SONGLIST_DIR = BASE_DIR / "songlist" / "Buckingham Conspiracy 3.0  SONG LIST"
SETLISTS_DIR = BASE_DIR / "setlists"

# Page configuration
st.set_page_config(
    page_title="🎸 Buckingham Conspiracy Hub",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for band styling
st.markdown("""
<style>
    /* Enhanced CSS for band hub */
    .main-header {
        background: linear-gradient(90deg, #033f57, #045a7a, #033f57);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    .song-card {
        background: linear-gradient(135deg, #2d2d2d, #3d3d3d);
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-left: 3px solid #B22222;
        color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1e1e1e, #2d2d2d);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #033f57;
        color: white;
    }
    
    .metric-title {
        font-size: 14px;
        color: #ccc;
        margin-bottom: 5px;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #045a7a;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(90deg, #1e1e1e, #2d2d2d);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #ccc;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #033f57, #045a7a);
        color: white;
    }
    
    .edit-song-form {
        background: linear-gradient(135deg, #2d2d2d, #3d3d3d);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #033f57;
    }
</style>
""", unsafe_allow_html=True)

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

# Utility functions
def load_song_list() -> Dict[str, Dict]:
    """Load the complete song list from markdown file"""
    song_file = SONGLIST_DIR / "Buckingham Conspiracy 3.0  SONG LIST.md"
    songs = {}
    
    try:
        with open(song_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse song entries using regex
        # Pattern matches: Song Name (BPM) or Song Name****^ ^****(BPM)
        song_pattern = r'^(.+?)(?:\*\*\*\*\^ \^\*\*\*\*)?\((\d+)\)'
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '(' in line:
                match = re.search(song_pattern, line)
                if match:
                    name = match.group(1).strip()
                    bpm = int(match.group(2))
                    
                    # Clean up song name
                    name = re.sub(r'\*\*\*\*\^ \^\*\*\*\*', '', name)
                    name = re.sub(r'\^.*?\^', '', name)  # Remove ^text^ annotations
                    name = name.strip()
                    
                    # Extract special markers
                    has_horn = '🎺' in line
                    has_vocals = '🥁' in line
                    
                    # Estimate duration based on BPM (rough calculation)
                    # Average song ~3.5 minutes, adjust based on BPM
                    base_duration = 210  # 3.5 minutes in seconds
                    duration_seconds = int(base_duration * (120 / max(bpm, 60)))  # Normalize to 120 BPM
                    
                    songs[name] = {
                        'bpm': bpm,
                        'duration': duration_seconds,
                        'has_horn': has_horn,
                        'has_vocals': has_vocals,
                        'energy_level': 'standard',  # Default energy level
                        'is_jam_vehicle': False,     # Default jam vehicle status
                        'raw_line': line
                    }
    except Exception as e:
        st.error(f"Error loading song list: {e}")
    
    return songs

def save_song_list(songs_data: Dict[str, Dict]):
    """Save the updated song list back to the markdown file"""
    song_file = SONGLIST_DIR / "Buckingham Conspiracy 3.0  SONG LIST.md"
    
    try:
        # Create the new content
        content = "# ****Buckingham Conspiracy 3.0 : SONG LIST ****  \n  \n#   \n"
        
        # Sort songs alphabetically
        for song_name in sorted(songs_data.keys()):
            song_info = songs_data[song_name]
            
            # Build the line with markers
            markers = ""
            if song_info.get('has_horn'):
                markers += "^🎺 ^"
            if song_info.get('has_vocals'):
                markers += "^🥁^"
            
            # Format the line
            line = f"{song_name}{markers} ({song_info['bpm']})"
            content += line + "  \n"
        
        content += "  \n  \n#   \n  \n"
        
        # Write back to file
        with open(song_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return True
    except Exception as e:
        st.error(f"Error saving song list: {e}")
        return False

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
                energy_level: str = 'standard', is_jam_vehicle: bool = False):
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

# Load data - Initialize if not in session state
if st.session_state.songs_data is None:
    st.session_state.songs_data = load_song_list()

songs_data = st.session_state.songs_data
previous_setlists = load_previous_setlists()

# Create tabs
tab1, tab2, tab3 = st.tabs(["📚 Song Library", "🎵 Setlist Builder", "📋 Previous Setlists"])

with tab1:
    st.header("📚 Song Library & Editor")
    
    if songs_data:
        # Display song statistics with new metadata
        total_songs = len(songs_data)
        horn_songs = len([s for s in songs_data.values() if s.get('has_horn')])
        vocal_songs = len([s for s in songs_data.values() if s.get('has_vocals')])
        jam_vehicles = len([s for s in songs_data.values() if s.get('is_jam_vehicle')])
        high_energy_songs = len([s for s in songs_data.values() if s.get('energy_level') == 'high'])
        avg_bpm = sum(s['bpm'] for s in songs_data.values()) / len(songs_data)
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
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
                <div class="metric-title">Horn Songs</div>
                <div class="metric-value">{horn_songs}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Vocal Songs</div>
                <div class="metric-value">{vocal_songs}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Jam Vehicles</div>
                <div class="metric-value">{jam_vehicles}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">High Energy</div>
                <div class="metric-value">{high_energy_songs}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col6:
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
                    new_energy_level = st.selectbox("Energy Level", get_energy_options(), 
                                                   index=1, key="add_song_energy")  # Default to 'standard'
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
            filter_type = st.selectbox("Filter by:", ["All Songs", "Horn Songs", "Vocal Songs", "Jam Vehicles", 
                                                     "High Energy", "Standard Energy", "Low Energy"], 
                                     key="song_library_filter")
        
        with col3:
            if st.button("🔄 Refresh Library", key="refresh_song_library"):
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
                    # First row: Song name and BPM
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        edited_name = st.text_input("Song Name", value=song_name, key=f"edit_name_{song_name}")
                    with col2:
                        edited_bpm = st.number_input("BPM", min_value=60, max_value=200, value=song_info['bpm'], key=f"edit_bpm_{song_name}")
                    
                    # Second row: Metadata
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        edited_horn = st.checkbox("Horn 🎺", value=song_info.get('has_horn', False), key=f"edit_horn_{song_name}")
                    with col2:
                        edited_vocals = st.checkbox("Vocals 🥁", value=song_info.get('has_vocals', False), key=f"edit_vocals_{song_name}")
                    with col3:
                        current_energy = song_info.get('energy_level', 'standard')
                        energy_index = get_energy_options().index(current_energy) if current_energy in get_energy_options() else 1
                        edited_energy = st.selectbox("Energy", get_energy_options(), index=energy_index, key=f"edit_energy_{song_name}")
                    with col4:
                        edited_jam = st.checkbox("Jam Vehicle 🎸", value=song_info.get('is_jam_vehicle', False), key=f"edit_jam_{song_name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes"):
                            if edited_name.strip():
                                if update_song(song_name, edited_name, edited_bpm, edited_horn, edited_vocals, 
                                              edited_energy, edited_jam):
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
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                
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
                    st.markdown(f"**{song_info['bpm']}** BPM")
                
                with col3:
                    st.markdown(f"**{format_duration(song_info['duration'])}**")
                
                with col4:
                    if st.button(f"✏️", key=f"edit_btn_{song_name}", help="Edit song"):
                        st.session_state.editing_song = song_name
                        st.rerun()
                
                with col5:
                    if st.button(f"🗑️", key=f"delete_btn_{song_name}", help="Delete song"):
                        if delete_song(song_name):
                            st.success(f"Deleted '{song_name}'!")
                            st.rerun()
                        else:
                            st.error("Failed to delete song.")
    else:
        st.error("No songs found. Please check the song list file.")

with tab2:
    st.header("🎵 Setlist Builder")
    
    # Setlist metadata
    col1, col2 = st.columns(2)
    with col1:
        venue = st.text_input("Venue", value=st.session_state.setlist_metadata['venue'], key="setlist_venue")
        st.session_state.setlist_metadata['venue'] = venue
    
    with col2:
        date = st.text_input("Date (MM/DD/YY)", value=st.session_state.setlist_metadata['date'], key="setlist_date")
        st.session_state.setlist_metadata['date'] = date
    
    # Set break durations
    col1, col2 = st.columns(2)
    with col1:
        set1_break = st.number_input("Set 1 Break (minutes)", value=15, min_value=0, max_value=60, key="set1_break")
        st.session_state.setlist_metadata['set_breaks']['set1_break'] = set1_break
    
    with col2:
        set2_break = st.number_input("Set 2 Break (minutes)", value=15, min_value=0, max_value=60, key="set2_break")
        st.session_state.setlist_metadata['set_breaks']['set2_break'] = set2_break
    
    # Song selector
    st.subheader("Add Songs to Sets")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # Create searchable song list
        song_names = list(songs_data.keys())
        selected_song = st.selectbox(
            "Select a song to add:",
            [""] + sorted(song_names),
            key="song_selector"
        )
    
    with col2:
        target_set = st.selectbox(
            "Add to set:",
            ["Set 1", "Set 2", "Set 3"],
            key="target_set"
        )
    
    # Add song button
    if st.button("➕ Add Song", key="add_song_to_setlist") and selected_song:
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
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        song_info = songs_data.get(song, {})
                        markers = ""
                        if song_info.get('has_horn'):
                            markers += "🎺 "
                        if song_info.get('has_vocals'):
                            markers += "🥁 "
                        
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
                st.info(f"No songs in {set_name} yet. Add some songs above!")
    
    # Export functionality
    st.markdown("---")
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

with tab3:
    st.header("📋 Previous Setlists")
    
    if previous_setlists:
        # Display filters
        venues = sorted(list(set(setlist['venue'] for setlist in previous_setlists)))
        selected_venue = st.selectbox("Filter by venue:", ["All Venues"] + venues, key="previous_setlists_venue_filter")
        
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
                
                # Edit form
                with st.form(f"edit_setlist_{setlist_id}"):
                    # Venue and date editing
                    col1, col2 = st.columns(2)
                    with col1:
                        edited_venue = st.text_input("Venue", value=st.session_state.edited_setlist_data['venue'], key=f"venue_{setlist_id}")
                    with col2:
                        edited_date = st.text_input("Date", value=st.session_state.edited_setlist_data['date'], key=f"date_{setlist_id}")
                    
                    # Edit sets
                    st.subheader("Edit Sets")
                    col1, col2, col3 = st.columns(3)
                    
                    for set_num, (col, set_name) in enumerate([(col1, "Set 1"), (col2, "Set 2"), (col3, "Set 3")], 1):
                        set_key = f"set{set_num}"
                        set_songs = st.session_state.edited_setlist_data['sets'].get(set_key, [])
                        
                        with col:
                            st.markdown(f"**{set_name}**")
                            
                            # Add song to set
                            song_names = list(songs_data.keys()) if songs_data else []
                            new_song = st.selectbox(f"Add song to {set_name}:", [""] + sorted(song_names), key=f"add_song_{set_key}_{setlist_id}")
                            
                            if st.form_submit_button(f"➕ Add to {set_name}", key=f"add_btn_{set_key}_{setlist_id}"):
                                if new_song and new_song not in [s['name'] for s in set_songs]:
                                    song_info = songs_data.get(new_song, {})
                                    set_songs.append({
                                        'name': new_song,
                                        'bpm': song_info.get('bpm'),
                                        'raw_line': f"{new_song} ({song_info.get('bpm', '')})" if song_info.get('bpm') else new_song
                                    })
                                    st.rerun()
                            
                            # Display and edit existing songs
                            for j, song in enumerate(set_songs):
                                song_col1, song_col2, song_col3 = st.columns([3, 1, 1])
                                
                                with song_col1:
                                    st.markdown(f"• {song['name']} ({song['bpm']})" if song['bpm'] else f"• {song['name']}")
                                
                                with song_col2:
                                    if st.form_submit_button("⬆️", key=f"up_{set_key}_{j}_{setlist_id}", disabled=j==0):
                                        set_songs[j], set_songs[j-1] = set_songs[j-1], set_songs[j]
                                        st.rerun()
                                
                                with song_col3:
                                    if st.form_submit_button("🗑️", key=f"del_{set_key}_{j}_{setlist_id}"):
                                        set_songs.pop(j)
                                        st.rerun()
                    
                    # Save/Cancel buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Setlist"):
                            # Update the setlist data
                            st.session_state.edited_setlist_data['venue'] = edited_venue
                            st.session_state.edited_setlist_data['date'] = edited_date
                            
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
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.editing_setlist = None
                            st.session_state.edited_setlist_data = None
                            st.rerun()
            
            else:
                # Display mode
                with st.expander(f"🎸 {setlist['venue']} - {setlist['date']}", expanded=False):
                    # Edit button
                    if st.button(f"✏️ Edit Setlist", key=f"edit_setlist_{setlist_id}"):
                        st.session_state.editing_setlist = setlist_id
                        st.session_state.edited_setlist_data = None  # Will be loaded in edit mode
                        st.rerun()
                    
                    col1, col2, col3 = st.columns(3)
                    
                    for set_num, (col, set_name) in enumerate([(col1, "Set 1"), (col2, "Set 2"), (col3, "Set 3")], 1):
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

# Sidebar with quick stats
st.sidebar.markdown("### 🎸 Quick Stats")
if st.session_state.current_setlist:
    total_songs_in_setlist = sum(len(songs) for songs in st.session_state.current_setlist.values())
    st.sidebar.metric("Songs in Current Setlist", total_songs_in_setlist)

st.sidebar.metric("Total Songs in Library", len(st.session_state.songs_data) if st.session_state.songs_data else 0)
st.sidebar.metric("Previous Setlists", len(previous_setlists))

st.sidebar.markdown("---")
st.sidebar.markdown("### Legend")
st.sidebar.markdown("🎺 = Horn parts")
st.sidebar.markdown("🥁 = Drum Vocal parts")
st.sidebar.markdown("🛸 = Jam vehicle")
st.sidebar.markdown("🔥 = High energy")
st.sidebar.markdown("💤 = Low energy")

if st.sidebar.button("🔄 Reload All Data"):
    st.session_state.songs_data = load_song_list()
    st.sidebar.success("Data reloaded!")
    st.rerun()
