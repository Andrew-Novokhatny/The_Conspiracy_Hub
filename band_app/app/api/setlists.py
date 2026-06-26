"""
Setlists API endpoints for band app
Previous setlist viewing, setlist building, and navigation
"""

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Dict, Any
from pathlib import Path
import json

# Import business logic
import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.setlist_manager import (
    load_previous_setlists,
    parse_setlist_file,
    save_setlist_to_file,
    calculate_set_timing,
    build_setlist_markdown,
    create_setlist_export_data,
    load_setlist_from_json,
    search_setlists_by_song,
    format_duration,
    human_readable_date
)
from core.song_manager import load_song_list

router = APIRouter()

# Setup templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/", response_class=HTMLResponse)
async def setlists_home(request: Request):
    """Main setlists page showing previous setlists"""
    try:
        previous_setlists = load_previous_setlists()

        return templates.TemplateResponse("setlists/index.html", {
            "request": request,
            "setlists": previous_setlists,
            "total_setlists": len(previous_setlists)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading setlists: {str(e)}")

@router.get("/list")
async def get_setlists_list(
    search_venue: Optional[str] = Query(None),
    search_song: Optional[str] = Query(None),
    limit: Optional[int] = Query(50)
):
    """Get list of previous setlists with optional filtering"""
    try:
        setlists = load_previous_setlists()

        # Apply filters
        if search_venue:
            venue_lower = search_venue.lower()
            setlists = [s for s in setlists if venue_lower in s['venue'].lower()]

        if search_song:
            # Search for setlists containing specific song
            song_matches = search_setlists_by_song(search_song)
            matching_setlist_files = {match['setlist']['file_path'] for match in song_matches}
            setlists = [s for s in setlists if s['file_path'] in matching_setlist_files]

        # Limit results
        if limit:
            setlists = setlists[:limit]

        return {
            "setlists": setlists,
            "total": len(setlists),
            "filters": {
                "search_venue": search_venue,
                "search_song": search_song,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading setlists list: {str(e)}")

@router.get("/{setlist_id}", response_class=HTMLResponse)
async def get_setlist_details(request: Request, setlist_id: int):
    """Get detailed view of a specific setlist"""
    try:
        setlists = load_previous_setlists()

        if setlist_id >= len(setlists) or setlist_id < 0:
            raise HTTPException(status_code=404, detail=f"Setlist {setlist_id} not found")

        setlist = setlists[setlist_id]
        songs_data = load_song_list()

        # Calculate set timings
        set_timings = {}
        total_show_seconds = 0

        for set_key, songs in setlist['sets'].items():
            song_names = [song['name'] for song in songs]
            set_seconds, formatted_duration = calculate_set_timing(song_names, songs_data)
            set_timings[set_key] = {
                'seconds': set_seconds,
                'formatted': formatted_duration,
                'song_count': len(songs)
            }
            total_show_seconds += set_seconds

        total_show_formatted = format_duration(total_show_seconds)

        return templates.TemplateResponse("setlists/details.html", {
            "request": request,
            "setlist": setlist,
            "setlist_id": setlist_id,
            "songs_data": songs_data,
            "set_timings": set_timings,
            "total_show_seconds": total_show_seconds,
            "total_show_formatted": total_show_formatted,
            "friendly_date": human_readable_date(setlist['date'])
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading setlist details: {str(e)}")

@router.get("/{setlist_id}/navigation", response_class=HTMLResponse)
async def get_setlist_navigation(request: Request, setlist_id: int, current_song: Optional[str] = Query(None)):
    """Get navigation controls for setlist progression"""
    try:
        setlists = load_previous_setlists()

        if setlist_id >= len(setlists) or setlist_id < 0:
            raise HTTPException(status_code=404, detail=f"Setlist {setlist_id} not found")

        setlist = setlists[setlist_id]

        # Build flat song list with set context
        all_songs = []
        for set_key, songs in setlist['sets'].items():
            for song in songs:
                all_songs.append({
                    'name': song['name'],
                    'set': set_key,
                    'bpm': song.get('bpm'),
                    'set_number': int(set_key[-1])
                })

        # Find current song position
        current_index = -1
        if current_song:
            for i, song in enumerate(all_songs):
                if song['name'] == current_song:
                    current_index = i
                    break

        # Calculate previous and next songs
        prev_song = all_songs[current_index - 1] if current_index > 0 else None
        next_song = all_songs[current_index + 1] if current_index < len(all_songs) - 1 else None

        return templates.TemplateResponse("setlists/navigation.html", {
            "request": request,
            "setlist": setlist,
            "setlist_id": setlist_id,
            "current_song": current_song,
            "current_index": current_index + 1,
            "total_songs": len(all_songs),
            "prev_song": prev_song,
            "next_song": next_song,
            "all_songs": all_songs
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading setlist navigation: {str(e)}")

@router.get("/search/song/{song_name}")
async def search_setlists_by_song_name(song_name: str):
    """Find all setlists containing a specific song"""
    try:
        matches = search_setlists_by_song(song_name)

        return {
            "song_name": song_name,
            "matches": matches,
            "total": len(matches)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching setlists: {str(e)}")

@router.get("/{setlist_id}/export")
async def export_setlist(setlist_id: int, format: str = Query("json")):
    """Export setlist in various formats"""
    try:
        setlists = load_previous_setlists()

        if setlist_id >= len(setlists) or setlist_id < 0:
            raise HTTPException(status_code=404, detail=f"Setlist {setlist_id} not found")

        setlist = setlists[setlist_id]

        if format == "json":
            # Build flat song list for export
            export_setlist = {
                "set1": [song['name'] for song in setlist['sets'].get('set1', [])],
                "set2": [song['name'] for song in setlist['sets'].get('set2', [])],
                "set3": [song['name'] for song in setlist['sets'].get('set3', [])]
            }

            export_data = create_setlist_export_data(
                setlist['venue'],
                setlist['date'],
                export_setlist
            )

            return export_data

        elif format == "markdown":
            songs_data = load_song_list()

            # Calculate set timings for markdown
            set_durations = {}
            total_show_seconds = 0

            for set_key, songs in setlist['sets'].items():
                song_names = [song['name'] for song in songs]
                set_seconds, formatted_duration = calculate_set_timing(song_names, songs_data)
                set_durations[f"{set_key}_duration"] = formatted_duration
                total_show_seconds += set_seconds

            set_durations['total_show'] = format_duration(total_show_seconds)

            # Build flat song list for markdown
            export_setlist = {
                "set1": [song['name'] for song in setlist['sets'].get('set1', [])],
                "set2": [song['name'] for song in setlist['sets'].get('set2', [])],
                "set3": [song['name'] for song in setlist['sets'].get('set3', [])]
            }

            markdown_content = build_setlist_markdown(
                setlist['venue'],
                setlist['date'],
                export_setlist,
                songs_data,
                set_durations,
                set_durations['total_show']
            )

            return {
                "venue": setlist['venue'],
                "date": setlist['date'],
                "markdown": markdown_content
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'markdown'")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting setlist: {str(e)}")

@router.get("/{setlist_id}/stats")
async def get_setlist_stats(setlist_id: int):
    """Get comprehensive statistics for a setlist"""
    try:
        setlists = load_previous_setlists()

        if setlist_id >= len(setlists) or setlist_id < 0:
            raise HTTPException(status_code=404, detail=f"Setlist {setlist_id} not found")

        setlist = setlists[setlist_id]
        songs_data = load_song_list()

        # Calculate detailed statistics
        total_songs = sum(len(songs) for songs in setlist['sets'].values())
        total_duration = 0
        energy_distribution = {"high": 0, "standard": 0, "low": 0}
        bpm_values = []
        horn_songs = 0
        jam_vehicles = 0

        set_stats = {}

        for set_key, songs in setlist['sets'].items():
            set_duration = 0
            set_song_count = len(songs)

            for song in songs:
                song_name = song['name']
                if song_name in songs_data:
                    song_info = songs_data[song_name]
                    duration = song_info.get('duration', 0)
                    total_duration += duration
                    set_duration += duration

                    energy_level = song_info.get('energy_level', 'standard')
                    energy_distribution[energy_level] += 1

                    bpm = song_info.get('bpm', 0)
                    if bpm:
                        bpm_values.append(bpm)

                    if song_info.get('has_horn', False):
                        horn_songs += 1

                    if song_info.get('is_jam_vehicle', False):
                        jam_vehicles += 1

            set_stats[set_key] = {
                'song_count': set_song_count,
                'duration_seconds': set_duration,
                'duration_formatted': format_duration(set_duration)
            }

        avg_bpm = sum(bpm_values) / len(bpm_values) if bpm_values else 0

        return {
            "setlist_id": setlist_id,
            "venue": setlist['venue'],
            "date": setlist['date'],
            "friendly_date": human_readable_date(setlist['date']),
            "total_songs": total_songs,
            "total_duration_seconds": total_duration,
            "total_duration_formatted": format_duration(total_duration),
            "avg_bpm": round(avg_bpm, 1),
            "energy_distribution": energy_distribution,
            "horn_songs": horn_songs,
            "jam_vehicles": jam_vehicles,
            "set_stats": set_stats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating setlist stats: {str(e)}")

@router.get("/{setlist_id}/songs/{set_name}")
async def get_setlist_set_songs(setlist_id: int, set_name: str):
    """Get songs from a specific set in a setlist"""
    try:
        if set_name not in ["set1", "set2", "set3"]:
            raise HTTPException(status_code=400, detail="Invalid set name. Use: set1, set2, set3")

        setlists = load_previous_setlists()

        if setlist_id >= len(setlists) or setlist_id < 0:
            raise HTTPException(status_code=404, detail=f"Setlist {setlist_id} not found")

        setlist = setlists[setlist_id]
        songs_in_set = setlist['sets'].get(set_name, [])
        songs_data = load_song_list()

        # Enhance song data
        enhanced_songs = []
        for song in songs_in_set:
            song_name = song['name']
            song_info = songs_data.get(song_name, {})

            enhanced_songs.append({
                'name': song_name,
                'bpm': song.get('bpm') or song_info.get('bpm', 0),
                'duration': song_info.get('duration', 0),
                'duration_formatted': format_duration(song_info.get('duration', 0)),
                'artist': song_info.get('artist', ''),
                'energy_level': song_info.get('energy_level', 'standard'),
                'has_horn': song_info.get('has_horn', False),
                'is_jam_vehicle': song_info.get('is_jam_vehicle', False)
            })

        return {
            "setlist_id": setlist_id,
            "set_name": set_name,
            "set_number": int(set_name[-1]),
            "songs": enhanced_songs,
            "song_count": len(enhanced_songs)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading set songs: {str(e)}")