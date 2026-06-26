"""
Lyrics API endpoints for band app
Mobile-optimized with HTMX support for smooth navigation
"""

from fastapi import APIRouter, Request, HTTPException, Query
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
    save_lyrics_content
)
from core.song_manager import load_song_list

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

@router.get("/{song_name}", response_class=HTMLResponse)
async def get_lyrics(request: Request, song_name: str):
    """Get lyrics for a specific song - HTMX compatible"""
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

        return templates.TemplateResponse(request=request, name="lyrics/display.html", context={
            "request": request,
            "song_name": song_name,
            "lyrics_content": formatted_lyrics,
            "artist": song_info.get('artist', ''),
            "bpm": song_info.get('bpm', ''),
            "duration": song_info.get('duration', ''),
            "fullscreen": False,
            "active_page": "lyrics",
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading lyrics: {str(e)}")

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

        # Return beautiful full-screen lyrics with teal theme
        return HTMLResponse(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>{song_name} - Full Screen</title>
    <link rel="stylesheet" href="/static/css/band-theme.css">
</head>
<body class="lyrics-fullscreen-container">
    <div class="lyrics-header">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div class="fade-in-up">
                <h1 class="band-title" style="font-size: 1.5rem; margin: 0;">{song_name}</h1>
                {f'<div class="text-muted" style="font-size: 0.9rem; margin-top: 0.25rem;">{artist}{" • " + str(bpm) + " BPM" if bpm else ""}</div>' if artist else ''}
            </div>
            <button class="band-btn" onclick="history.back()" style="padding: 0.5rem 1rem;">
                ↩️ Exit
            </button>
        </div>
    </div>

    <div class="lyrics-content fade-in-up">
        {formatted_lyrics}
    </div>

    <script>
        let isExiting = false;

        // Escape key to exit
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape' && !isExiting) {{
                isExiting = true;
                history.back();
            }}
        }});

        // Double-tap to exit (optional)
        let lastTap = 0;
        document.addEventListener('touchend', function(e) {{
            const currentTime = new Date().getTime();
            const tapLength = currentTime - lastTap;

            if (tapLength < 500 && tapLength > 0 && !isExiting) {{
                const result = confirm('Exit full screen?');
                if (result) {{
                    isExiting = true;
                    history.back();
                }}
            }}
            lastTap = currentTime;
        }});

        // Prevent zoom on double-tap
        document.addEventListener('touchend', function(e) {{
            e.preventDefault();
        }}, {{ passive: false }});
    </script>
</body>
</html>""")
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