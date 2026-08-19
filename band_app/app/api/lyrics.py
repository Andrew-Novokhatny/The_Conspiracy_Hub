"""
Lyrics API endpoints for band app
Mobile-optimized with HTMX support for smooth navigation
"""

from fastapi import APIRouter, Request, HTTPException, Query, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pathlib import Path

# Import business logic
import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.lyrics_manager import (
    load_available_lyrics,
    load_lyrics_content,
    format_lyrics_for_display,
    search_lyrics,
    save_lyrics_content,
    delete_lyrics_file
)
from core.song_manager import load_song_list, delete_song_from_catalog
from core.lyrics_fetcher import fetch_lyrics_online

router = APIRouter()

# Setup templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/", response_class=HTMLResponse)
async def lyrics_home(request: Request):
    """Main lyrics page with song selection"""
    try:
        available_lyrics = load_available_lyrics()
        songs_data = load_song_list()

        return templates.TemplateResponse(request=request, name="lyrics/index.html", context={
            "request": request,
            "available_lyrics": available_lyrics,
            "songs_data": songs_data,
            "total_lyrics": len(available_lyrics),
            "active_page": "lyrics",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading lyrics: {str(e)}")

@router.get("/list")
async def get_lyrics_list(search: Optional[str] = Query(None)):
    """Get list of available lyrics with optional search"""
    try:
        available_lyrics = load_available_lyrics()

        if search:
            # Filter by search term in song name
            search_lower = search.lower()
            available_lyrics = [
                song for song in available_lyrics
                if search_lower in song.lower()
            ]

        return {
            "lyrics": available_lyrics,
            "total": len(available_lyrics),
            "search_term": search
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading lyrics list: {str(e)}")


@router.get("/fetch-modal", response_class=HTMLResponse)
async def get_fetch_lyrics_modal(request: Request):
    """Render fetch lyrics modal with missing songs from catalog"""
    try:
        available_lyrics = set(load_available_lyrics())
        songs_data = load_song_list()
        
        # Prioritize songs in catalog that don't yet have lyrics
        missing_catalog_songs = {
            name: info for name, info in songs_data.items()
            if name not in available_lyrics
        }
        if not missing_catalog_songs:
            missing_catalog_songs = songs_data

        return templates.TemplateResponse(request=request, name="lyrics/fetch_modal.html", context={
            "request": request,
            "catalog_songs": missing_catalog_songs,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading fetch modal: {str(e)}")


@router.post("/fetch-preview", response_class=HTMLResponse)
async def fetch_lyrics_preview(
    request: Request,
    title: str = Form(""),
    artist: str = Form("")
):
    """Fetch lyrics from Genius and return preview partial"""
    try:
        title = title.strip()
        artist = artist.strip()
        if not title:
            return templates.TemplateResponse(request=request, name="lyrics/fetch_preview_partial.html", context={
                "request": request,
                "success": False,
                "lyrics": "",
                "error": "Please enter a song title to search.",
            })

        res = fetch_lyrics_online(title, artist)
        return templates.TemplateResponse(request=request, name="lyrics/fetch_preview_partial.html", context={
            "request": request,
            "success": res.get("success", False),
            "lyrics": res.get("lyrics", ""),
            "matched_title": res.get("matched_title", title),
            "matched_artist": res.get("matched_artist", artist),
            "source_url": res.get("source_url", ""),
            "error": res.get("error"),
        })
    except Exception as e:
        return templates.TemplateResponse(request=request, name="lyrics/fetch_preview_partial.html", context={
            "request": request,
            "success": False,
            "lyrics": "",
            "error": f"Error fetching lyrics: {str(e)}",
        })


@router.post("/save-new")
async def save_new_lyrics(
    request: Request,
    title: str = Form(""),
    song_name: Optional[str] = Form(None),
    lyrics_content: str = Form("")
):
    """Save newly fetched or edited lyrics to disk"""
    target_song = (title or song_name or "").strip()
    if not target_song:
        raise HTTPException(status_code=400, detail="Song title is required")
    
    if not lyrics_content.strip():
        raise HTTPException(status_code=400, detail="Lyrics content cannot be empty")

    save_lyrics_content(target_song, lyrics_content.strip())
    
    return HTMLResponse(
        content=f"<script>window.location.href='/api/lyrics/{target_song}';</script>",
        headers={"HX-Redirect": f"/api/lyrics/{target_song}"}
    )


@router.post("/{song_name}/delete")
@router.delete("/{song_name}")
async def delete_lyrics_and_song_endpoint(request: Request, song_name: str):
    """Permanently delete a song from lyrics and catalog"""
    try:
        delete_song_from_catalog(song_name)
        delete_lyrics_file(song_name)
        
        return HTMLResponse(
            content="<script>window.location.href='/api/lyrics/';</script>",
            headers={"HX-Redirect": "/api/lyrics/"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting song: {str(e)}")


@router.get("/{song_name}", response_class=HTMLResponse)
async def get_lyrics(request: Request, song_name: str):
    """Get lyrics for a specific song - HTMX compatible"""
    try:
        # Load lyrics content
        lyrics_content = load_lyrics_content(song_name)

        if "not found" in lyrics_content.lower() or not lyrics_content.strip():
            formatted_lyrics = ""
        else:
            # Format for HTML display
            formatted_lyrics = format_lyrics_for_display(lyrics_content)

        # Get song info if available
        songs_data = load_song_list()
        song_info = songs_data.get(song_name, {})
        duration_sec = song_info.get('duration', 0)
        duration_formatted = f"{duration_sec // 60}:{(duration_sec % 60):02d}" if duration_sec else ""

        return templates.TemplateResponse(request=request, name="lyrics/display.html", context={
            "request": request,
            "song_name": song_name,
            "lyrics_content": formatted_lyrics,
            "song_info": song_info,
            "artist": song_info.get('artist', ''),
            "bpm": song_info.get('bpm', ''),
            "song_key": song_info.get('song_key', ''),
            "duration": duration_sec,
            "duration_formatted": duration_formatted,
            "has_horn": song_info.get('has_horn', False),
            "is_jam_vehicle": song_info.get('is_jam_vehicle', False),
            "energy_level": song_info.get('energy_level', 'standard'),
            "fullscreen": False,
            "active_page": "lyrics",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading lyrics: {str(e)}")


@router.get("/{song_name}/view_partial", response_class=HTMLResponse)
async def get_lyrics_view_partial(request: Request, song_name: str):
    """Get partial view of lyrics (just the content inside container)"""
    try:
        lyrics_content = load_lyrics_content(song_name)
        if "not found" in lyrics_content.lower() or not lyrics_content.strip():
            formatted_lyrics = ""
        else:
            formatted_lyrics = format_lyrics_for_display(lyrics_content)

        songs_data = load_song_list()
        song_info = songs_data.get(song_name, {})
        duration_sec = song_info.get('duration', 0)
        duration_formatted = f"{duration_sec // 60}:{(duration_sec % 60):02d}" if duration_sec else ""

        return templates.TemplateResponse(request=request, name="lyrics/display_partial.html", context={
            "request": request,
            "song_name": song_name,
            "lyrics_content": formatted_lyrics,
            "song_info": song_info,
            "artist": song_info.get('artist', ''),
            "bpm": song_info.get('bpm', ''),
            "song_key": song_info.get('song_key', ''),
            "duration": duration_sec,
            "duration_formatted": duration_formatted,
            "has_horn": song_info.get('has_horn', False),
            "is_jam_vehicle": song_info.get('is_jam_vehicle', False),
            "energy_level": song_info.get('energy_level', 'standard'),
            "active_page": "lyrics",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading lyrics partial: {str(e)}")


@router.get("/{song_name}/edit", response_class=HTMLResponse)
async def get_lyrics_edit(request: Request, song_name: str):
    """Get partial edit form for lyrics"""
    try:
        lyrics_content = load_lyrics_content(song_name)
        if "not found" in lyrics_content.lower():
            lyrics_content = ""

        songs_data = load_song_list()
        song_info = songs_data.get(song_name, {})

        return templates.TemplateResponse(request=request, name="lyrics/edit_partial.html", context={
            "request": request,
            "song_name": song_name,
            "raw_lyrics": lyrics_content,
            "artist": song_info.get('artist', ''),
            "active_page": "lyrics",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading lyrics edit form: {str(e)}")


@router.post("/{song_name}/edit", response_class=HTMLResponse)
async def post_lyrics_edit(request: Request, song_name: str, lyrics: str = Form("")):
    """Save edited lyrics and return the display partial"""
    try:
        # Save to file (which persists to mounted directory via lyrics_manager)
        save_lyrics_content(song_name, lyrics)

        # Reload and format
        lyrics_content = load_lyrics_content(song_name)
        formatted_lyrics = format_lyrics_for_display(lyrics_content)

        songs_data = load_song_list()
        song_info = songs_data.get(song_name, {})

        return templates.TemplateResponse(request=request, name="lyrics/display_partial.html", context={
            "request": request,
            "song_name": song_name,
            "lyrics_content": formatted_lyrics,
            "artist": song_info.get('artist', ''),
            "bpm": song_info.get('bpm', ''),
            "song_key": song_info.get('song_key', ''),
            "duration": song_info.get('duration', ''),
            "active_page": "lyrics",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving lyrics: {str(e)}")

@router.get("/{song_name}/fullscreen", response_class=HTMLResponse)
async def get_lyrics_fullscreen(request: Request, song_name: str):
    """Get lyrics in full-screen mode - optimized for mobile performance"""
    try:
        # Load lyrics content
        lyrics_content = load_lyrics_content(song_name)

        if "not found" in lyrics_content.lower():
            raise HTTPException(status_code=404, detail=f"Lyrics for '{song_name}' not found")

        # Format for HTML display
        formatted_lyrics = format_lyrics_for_display(lyrics_content)

        # Get song info if available
        songs_data = load_song_list()
        song_info = songs_data.get(song_name, {})

        artist = song_info.get('artist', '')
        bpm = song_info.get('bpm', '')

        duration = song_info.get('duration', 0)
        duration_formatted = f"{duration // 60}:{(duration % 60):02d}" if duration else ""
        if not duration or duration <= 0:
            duration = 240

        return templates.TemplateResponse(request=request, name="lyrics/fullscreen.html", context={
            "request": request,
            "song_name": song_name,
            "lyrics_content": formatted_lyrics,
            "song_info": song_info,
            "artist": song_info.get('artist', ''),
            "bpm": song_info.get('bpm', ''),
            "song_key": song_info.get('song_key', ''),
            "duration": duration,
            "duration_formatted": duration_formatted,
            "has_horn": song_info.get('has_horn', False),
            "is_jam_vehicle": song_info.get('is_jam_vehicle', False),
            "energy_level": song_info.get('energy_level', 'standard'),
            "active_page": "lyrics",
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading fullscreen lyrics: {str(e)}")

@router.get("/{song_name}/raw")
async def get_lyrics_raw(song_name: str):
    """Get raw lyrics content as JSON"""
    try:
        lyrics_content = load_lyrics_content(song_name)

        if "not found" in lyrics_content.lower():
            raise HTTPException(status_code=404, detail=f"Lyrics for '{song_name}' not found")

        # Get song info if available
        songs_data = load_song_list()
        song_info = songs_data.get(song_name, {})

        return {
            "song_name": song_name,
            "lyrics": lyrics_content,
            "formatted_lyrics": format_lyrics_for_display(lyrics_content),
            "artist": song_info.get('artist', ''),
            "bpm": song_info.get('bpm', ''),
            "duration": song_info.get('duration', ''),
            "energy_level": song_info.get('energy_level', 'standard'),
            "has_horn": song_info.get('has_horn', False)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading lyrics: {str(e)}")

@router.get("/search/{query}")
async def search_lyrics_content(query: str):
    """Search for songs by lyrics content"""
    try:
        matching_songs = search_lyrics(query)

        return {
            "query": query,
            "matches": matching_songs,
            "total": len(matching_songs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching lyrics: {str(e)}")

@router.get("/{song_name}/navigation", response_class=HTMLResponse)
async def get_lyrics_navigation(request: Request, song_name: str, context: Optional[str] = Query(None)):
    """Get navigation controls for lyrics - supports setlist context"""
    try:
        available_lyrics = load_available_lyrics()

        # Find current song index
        current_index = -1
        if song_name in available_lyrics:
            current_index = available_lyrics.index(song_name)

        # Calculate previous and next songs
        prev_song = None
        next_song = None

        if context == "setlist":
            # TODO: Implement setlist-based navigation
            # For now, use alphabetical navigation
            pass

        # Default alphabetical navigation
        if current_index > 0:
            prev_song = available_lyrics[current_index - 1]
        if current_index < len(available_lyrics) - 1:
            next_song = available_lyrics[current_index + 1]

        return templates.TemplateResponse(request=request, name="lyrics/navigation.html", context={
            "request": request,
            "current_song": song_name,
            "prev_song": prev_song,
            "next_song": next_song,
            "context": context,
            "current_index": current_index + 1,
            "total_songs": len(available_lyrics),
            "active_page": "lyrics",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading navigation: {str(e)}")