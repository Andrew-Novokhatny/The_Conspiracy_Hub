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
    combine_avg_length,
    derive_song_duration,
    delete_song_from_catalog
)
from core.lyrics_manager import load_available_lyrics, save_lyrics_content, delete_lyrics_file
from core.lyrics_fetcher import fetch_lyrics_online
from core.utils import load_available_tabs

router = APIRouter()

# Setup templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def parse_time_string(val: str) -> Optional[int]:
    if not val:
        return None
    val = val.strip()
    if ":" in val:
        parts = val.split(":")
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except (ValueError, IndexError):
            return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

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


@router.get("/add-modal", response_class=HTMLResponse)
async def get_add_song_modal(request: Request):
    """Render Add Song Modal"""
    return templates.TemplateResponse(request=request, name="songs/add_modal.html", context={"request": request})


@router.post("/add")
async def add_new_song(
    request: Request,
    title: str = Form(...),
    artist: str = Form(""),
    bpm: int = Form(120),
    song_key: str = Form(""),
    avg_length: str = Form(""),
    energy_level: str = Form("standard"),
    has_horn: Optional[bool] = Form(False),
    is_jam_vehicle: Optional[bool] = Form(False),
    auto_fetch_lyrics: Optional[bool] = Form(False),
    lyrics_content: Optional[str] = Form(None)
):
    """Add new song to the catalog and optionally fetch/save its lyrics"""
    clean_title = title.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Song title is required")

    songs_data = load_song_list()
    
    parsed_length = parse_time_string(avg_length)
    duration_sec = derive_song_duration(bpm, parsed_length)

    songs_data[clean_title] = {
        "bpm": bpm,
        "song_key": song_key.strip(),
        "duration": duration_sec,
        "has_horn": bool(has_horn),
        "energy_level": energy_level.strip().lower() if energy_level.strip().lower() in {"high", "standard", "low"} else "standard",
        "is_jam_vehicle": bool(is_jam_vehicle),
        "artist": artist.strip(),
        "avg_length": parsed_length,
        "raw_line": f"{clean_title} ({bpm})",
    }

    # 1. Save metadata to CSV and Markdown
    save_song_list(songs_data)

    # 2. Save or fetch lyrics
    if lyrics_content and lyrics_content.strip():
        save_lyrics_content(clean_title, lyrics_content.strip())
    elif auto_fetch_lyrics:
        try:
            fetched = fetch_lyrics_online(clean_title, artist.strip())
            if fetched.get("success") and fetched.get("lyrics"):
                save_lyrics_content(clean_title, fetched["lyrics"])
        except Exception as e:
            print(f"Auto-fetch lyrics exception for '{clean_title}': {e}")

    return HTMLResponse(
        content="<script>window.location.href='/api/songs/';</script>",
        headers={"HX-Redirect": "/api/songs/"}
    )


@router.post("/{song_name}/delete")
@router.delete("/{song_name}")
async def delete_song_endpoint(request: Request, song_name: str):
    """Permanently delete a song from catalog and its lyrics file"""
    try:
        delete_song_from_catalog(song_name)
        delete_lyrics_file(song_name)
        
        return HTMLResponse(
            content="<script>window.location.href='/api/lyrics/';</script>",
            headers={"HX-Redirect": "/api/lyrics/"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting song: {str(e)}")


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
            "song_key": song_info.get('song_key', ''),
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


@router.get("/{song_name}/row", response_class=HTMLResponse)
async def get_song_row(request: Request, song_name: str):
    """Get HTML row for a specific song - HTMX compatible"""
    try:
        songs_data = load_song_list()
        if song_name not in songs_data:
            raise HTTPException(status_code=404, detail=f"Song '{song_name}' not found")

        song_info = songs_data[song_name]
        available_lyrics = load_available_lyrics()
        has_lyrics = song_name in available_lyrics

        duration_minutes, duration_seconds = split_minutes_seconds(song_info.get('duration', 0))

        return templates.TemplateResponse(request=request, name="songs/row_partial.html", context={
            "request": request,
            "song_name": song_name,
            "song_info": song_info,
            "duration_formatted": f"{duration_minutes:02d}:{duration_seconds:02d}",
            "has_lyrics": has_lyrics,
            "active_page": "songs",
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading song row: {str(e)}")


@router.get("/{song_name}/edit", response_class=HTMLResponse)
async def get_edit_song_form(
    request: Request,
    song_name: str,
    context: Optional[str] = Query("card")
):
    """Return the edit form for a specific song."""
    try:
        songs_data = load_song_list()
        
        if song_name not in songs_data:
            raise HTTPException(status_code=404, detail="Song not found")
            
        song_info = songs_data[song_name]
        
        avg_len_seconds = song_info.get('avg_length') or song_info.get('duration')
        avg_len_formatted = ""
        if avg_len_seconds:
            m, s = split_minutes_seconds(avg_len_seconds)
            avg_len_formatted = f"{m}:{s:02d}"

        return templates.TemplateResponse(request=request, name="songs/edit.html", context={
            "request": request,
            "song_name": song_name,
            "song_info": song_info,
            "avg_len_formatted": avg_len_formatted,
            "context_type": context,
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
    song_key: str = Form(""),
    has_horn: bool = Form(False),
    is_jam_vehicle: bool = Form(False),
    energy_level: str = Form("standard"),
    avg_length: Optional[str] = Form(""),
    context_type: Optional[str] = Form("card")
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
                raw_str = str(avg_length).strip()
                if ':' in raw_str:
                    m, s = raw_str.split(':', 1)
                    avg_length_seconds = int(m) * 60 + int(s)
                elif raw_str:
                    avg_length_seconds = int(float(raw_str))
            except ValueError:
                avg_length_seconds = None
                
        # Update metadata dictionary
        songs_data[song_name].update({
            "artist": artist.strip(),
            "bpm": bpm,
            "song_key": song_key.strip(),
            "has_horn": has_horn,
            "is_jam_vehicle": is_jam_vehicle,
            "energy_level": energy_level,
            "avg_length": avg_length_seconds
        })
        
        # Save to persistent storage (CSV + Markdown on mounted disk)
        save_success = save_song_list(songs_data)
        if not save_success:
            raise Exception("Failed to save to CSV/Markdown")
            
        song_info = songs_data[song_name]
        from core.song_manager import derive_song_duration
        song_info['duration'] = derive_song_duration(bpm, avg_length_seconds)
        duration_minutes, duration_seconds = split_minutes_seconds(song_info['duration'])
        duration_formatted = f"{duration_minutes:02d}:{duration_seconds:02d}"

        has_lyrics = song_name in load_available_lyrics()
        has_tabs = any(tab for tab in load_available_tabs() if song_name.lower() in tab.lower())

        if context_type == "row":
            return templates.TemplateResponse(request=request, name="songs/row_partial.html", context={
                "request": request,
                "song_name": song_name,
                "song_info": song_info,
                "duration_formatted": duration_formatted,
                "has_lyrics": has_lyrics,
                "active_page": "songs",
            })
        elif context_type == "lyrics":
            from core.lyrics_manager import load_lyrics_content, format_lyrics_for_display
            raw_lyrics = load_lyrics_content(song_name)
            lyrics_html = format_lyrics_for_display(raw_lyrics) if "not found" not in raw_lyrics.lower() else ""

            return templates.TemplateResponse(request=request, name="lyrics/display_partial.html", context={
                "request": request,
                "song_name": song_name,
                "artist": song_info.get('artist', ''),
                "bpm": song_info.get('bpm', 120),
                "song_key": song_info.get('song_key', ''),
                "duration": song_info.get('duration', 0),
                "lyrics_content": lyrics_html,
                "active_page": "lyrics",
            })
        else:
            return templates.TemplateResponse(request=request, name="songs/card.html", context={
                "request": request,
                "song_name": song_name,
                "song_info": song_info,
                "duration_formatted": duration_formatted,
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