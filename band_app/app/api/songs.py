"""
Songs API endpoints for band app
Library management, filtering, and song data access
"""

from fastapi import APIRouter, Request, HTTPException, Query, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Dict, Any
from pathlib import Path

# Import business logic
import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.song_manager import (
    load_song_list,
    get_song_stats,
    save_song_list,
    split_minutes_seconds,
    combine_avg_length
)
from core.lyrics_manager import load_available_lyrics
from core.utils import load_available_tabs

router = APIRouter()

# Setup templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/", response_class=HTMLResponse)
async def songs_home(request: Request):
    """Main songs library page"""
    try:
        songs_data = load_song_list()
        stats = get_song_stats(songs_data)
        available_lyrics = load_available_lyrics()
        available_tabs = load_available_tabs()

        return templates.TemplateResponse(request=request, name="songs/index.html", context={
            "request": request,
            "songs": songs_data,
            "stats": stats,
            "available_lyrics": available_lyrics,
            "available_tabs": available_tabs,
            "active_page": "songs",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading songs library: {str(e)}")

@router.get("/list")
async def get_songs_list(
    search: Optional[str] = Query(None),
    energy_level: Optional[str] = Query(None),
    has_horn: Optional[bool] = Query(None),
    is_jam_vehicle: Optional[bool] = Query(None),
    min_bpm: Optional[int] = Query(None),
    max_bpm: Optional[int] = Query(None),
    sort_by: Optional[str] = Query("title"),  # title, bpm, artist, duration
    sort_order: Optional[str] = Query("asc")  # asc, desc
):
    """Get filtered and sorted songs list"""
    try:
        songs_data = load_song_list()

        # Apply filters
        filtered_songs = {}

        for song_name, song_info in songs_data.items():
            # Search filter
            if search:
                search_lower = search.lower()
                if not (search_lower in song_name.lower() or
                       search_lower in song_info.get('artist', '').lower()):
                    continue

            # Energy level filter
            if energy_level and song_info.get('energy_level') != energy_level:
                continue

            # Horn filter
            if has_horn is not None and song_info.get('has_horn') != has_horn:
                continue

            # Jam vehicle filter
            if is_jam_vehicle is not None and song_info.get('is_jam_vehicle') != is_jam_vehicle:
                continue

            # BPM range filters
            song_bpm = song_info.get('bpm', 0)
            if min_bpm and song_bpm < min_bpm:
                continue
            if max_bpm and song_bpm > max_bpm:
                continue

            filtered_songs[song_name] = song_info

        # Sort results
        sort_reverse = sort_order == "desc"

        if sort_by == "title":
            sorted_items = sorted(filtered_songs.items(),
                                key=lambda x: x[0].lower(), reverse=sort_reverse)
        elif sort_by == "artist":
            sorted_items = sorted(filtered_songs.items(),
                                key=lambda x: x[1].get('artist', '').lower(), reverse=sort_reverse)
        elif sort_by == "bpm":
            sorted_items = sorted(filtered_songs.items(),
                                key=lambda x: x[1].get('bpm', 0), reverse=sort_reverse)
        elif sort_by == "duration":
            sorted_items = sorted(filtered_songs.items(),
                                key=lambda x: x[1].get('duration', 0), reverse=sort_reverse)
        else:
            sorted_items = list(filtered_songs.items())

        result_songs = dict(sorted_items)

        return {
            "songs": result_songs,
            "total": len(result_songs),
            "filters": {
                "search": search,
                "energy_level": energy_level,
                "has_horn": has_horn,
                "is_jam_vehicle": is_jam_vehicle,
                "min_bpm": min_bpm,
                "max_bpm": max_bpm,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering songs: {str(e)}")

@router.get("/{song_name}")
async def get_song_details(song_name: str):
    """Get detailed information about a specific song"""
    try:
        songs_data = load_song_list()

        if song_name not in songs_data:
            raise HTTPException(status_code=404, detail=f"Song '{song_name}' not found")

        song_info = songs_data[song_name]

        # Check if lyrics and tabs are available
        available_lyrics = load_available_lyrics()
        available_tabs = load_available_tabs()

        has_lyrics = song_name in available_lyrics
        has_tabs = any(tab for tab in available_tabs if song_name.lower() in tab.lower())

        # Format duration
        duration_minutes, duration_seconds = split_minutes_seconds(song_info.get('duration', 0))

        return {
            "song_name": song_name,
            "artist": song_info.get('artist', ''),
            "bpm": song_info.get('bpm', 0),
            "duration": song_info.get('duration', 0),
            "duration_formatted": f"{duration_minutes:02d}:{duration_seconds:02d}",
            "energy_level": song_info.get('energy_level', 'standard'),
            "has_horn": song_info.get('has_horn', False),
            "is_jam_vehicle": song_info.get('is_jam_vehicle', False),
            "avg_length": song_info.get('avg_length'),
            "has_lyrics": has_lyrics,
            "has_tabs": has_tabs,
            "raw_line": song_info.get('raw_line', '')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading song details: {str(e)}")

@router.get("/{song_name}/card", response_class=HTMLResponse)
async def get_song_card(request: Request, song_name: str):
    """Get HTML card for a specific song - HTMX compatible"""
    try:
        songs_data = load_song_list()

        if song_name not in songs_data:
            raise HTTPException(status_code=404, detail=f"Song '{song_name}' not found")

        song_info = songs_data[song_name]

        # Check availability of related content
        available_lyrics = load_available_lyrics()
        available_tabs = load_available_tabs()

        has_lyrics = song_name in available_lyrics
        has_tabs = any(tab for tab in available_tabs if song_name.lower() in tab.lower())

        # Format duration
        duration_minutes, duration_seconds = split_minutes_seconds(song_info.get('duration', 0))

        return templates.TemplateResponse(request=request, name="songs/card.html", context={
            "request": request,
            "song_name": song_name,
            "song_info": song_info,
            "duration_formatted": f"{duration_minutes:02d}:{duration_seconds:02d}",
            "has_lyrics": has_lyrics,
            "has_tabs": has_tabs,
            "active_page": "songs",
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading song: {str(e)}")


@router.get("/{song_name}/edit", response_class=HTMLResponse)
async def get_edit_song_form(request: Request, song_name: str):
    """Return the edit form for a specific song."""
    try:
        songs_data = load_song_list()
        
        if song_name not in songs_data:
            raise HTTPException(status_code=404, detail="Song not found")
            
        song_info = songs_data[song_name]
        
        return templates.TemplateResponse(request=request, name="songs/edit.html", context={
            "request": request,
            "song_name": song_name,
            "song_info": song_info,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading song for edit: {str(e)}")


@router.post("/{song_name}/edit", response_class=HTMLResponse)
async def save_edited_song(
    request: Request,
    song_name: str,
    artist: str = Form(""),
    bpm: int = Form(120),
    has_horn: bool = Form(False),
    is_jam_vehicle: bool = Form(False),
    energy_level: str = Form("standard"),
    avg_length: str = Form(None)
):
    """Save edited song metadata."""
    try:
        songs_data = load_song_list()
        
        if song_name not in songs_data:
            raise HTTPException(status_code=404, detail="Song not found")
            
        # Parse average length back to seconds if provided
        avg_length_seconds = None
        if avg_length:
            try:
                # If they enter '4:30', parse it. Or if they enter '270', parse it.
                if ':' in avg_length:
                    m, s = avg_length.split(':', 1)
                    avg_length_seconds = int(m) * 60 + int(s)
                else:
                    avg_length_seconds = int(avg_length)
            except ValueError:
                pass # fall back to None or whatever is derived
                
        # Update metadata
        songs_data[song_name].update({
            "artist": artist.strip(),
            "bpm": bpm,
            "has_horn": has_horn,
            "is_jam_vehicle": is_jam_vehicle,
            "energy_level": energy_level,
            "avg_length": avg_length_seconds
        })
        
        # Save to disk
        save_success = save_song_list(songs_data)
        if not save_success:
            raise Exception("Failed to save to CSV/Markdown")
            
        # Return the read-only card to replace the form via HTMX
        # Redirect to the card route or just render it here.
        # Since we use HTMX, we can just return the updated card HTML.
        
        song_info = songs_data[song_name]
        from core.song_manager import derive_song_duration
        song_info['duration'] = derive_song_duration(bpm, avg_length_seconds)
        
        duration_minutes, duration_seconds = split_minutes_seconds(song_info['duration'])
        
        has_lyrics = song_name in load_available_lyrics()
        has_tabs = any(tab for tab in load_available_tabs() if song_name.lower() in tab.lower())
        
        return templates.TemplateResponse(request=request, name="songs/card.html", context={
            "request": request,
            "song_name": song_name,
            "song_info": song_info,
            "duration_formatted": f"{duration_minutes:02d}:{duration_seconds:02d}",
            "has_lyrics": has_lyrics,
            "has_tabs": has_tabs,
            "active_page": "songs",
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving song metadata: {str(e)}")

@router.get("/stats/overview")
async def get_song_stats_overview():
    """Get comprehensive statistics about the song library"""
    try:
        songs_data = load_song_list()
        stats = get_song_stats(songs_data)

        # Additional statistics
        bpm_ranges = {
            "slow": len([s for s in songs_data.values() if s.get('bpm', 0) < 90]),
            "medium": len([s for s in songs_data.values() if 90 <= s.get('bpm', 0) < 130]),
            "fast": len([s for s in songs_data.values() if s.get('bpm', 0) >= 130])
        }

        # Duration statistics
        total_duration = sum(s.get('duration', 0) for s in songs_data.values())
        avg_duration = total_duration / len(songs_data) if songs_data else 0

        duration_minutes, duration_seconds = split_minutes_seconds(int(avg_duration))

        return {
            **stats,
            "bpm_ranges": bpm_ranges,
            "total_duration_seconds": total_duration,
            "total_duration_formatted": f"{total_duration // 3600:02d}:{(total_duration % 3600) // 60:02d}:{total_duration % 60:02d}",
            "avg_duration_seconds": avg_duration,
            "avg_duration_formatted": f"{duration_minutes:02d}:{duration_seconds:02d}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading song statistics: {str(e)}")

@router.get("/energy/{energy_level}")
async def get_songs_by_energy(energy_level: str):
    """Get songs filtered by energy level"""
    try:
        if energy_level not in ["high", "standard", "low"]:
            raise HTTPException(status_code=400, detail="Invalid energy level. Use: high, standard, low")

        songs_data = load_song_list()
        filtered_songs = {
            name: info for name, info in songs_data.items()
            if info.get('energy_level') == energy_level
        }

        return {
            "energy_level": energy_level,
            "songs": filtered_songs,
            "total": len(filtered_songs)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering by energy level: {str(e)}")

@router.get("/horn/songs")
async def get_horn_songs():
    """Get all songs that feature horn sections"""
    try:
        songs_data = load_song_list()
        horn_songs = {
            name: info for name, info in songs_data.items()
            if info.get('has_horn', False)
        }

        return {
            "horn_songs": horn_songs,
            "total": len(horn_songs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading horn songs: {str(e)}")

@router.get("/jam/vehicles")
async def get_jam_vehicles():
    """Get all songs marked as jam vehicles"""
    try:
        songs_data = load_song_list()
        jam_vehicles = {
            name: info for name, info in songs_data.items()
            if info.get('is_jam_vehicle', False)
        }

        return {
            "jam_vehicles": jam_vehicles,
            "total": len(jam_vehicles)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading jam vehicles: {str(e)}")