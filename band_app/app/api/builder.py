"""
Setlist Builder API endpoints
Drag and drop interactive builder with live math
"""

from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json
import os

# Import business logic
import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.song_manager import load_song_list
from core.setlist_manager import save_setlist_to_file, SETLISTS_DIR

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/", response_class=HTMLResponse)
async def get_builder(request: Request):
    """Render the Setlist Builder UI"""
    try:
        songs_data = load_song_list()
        
        # Sort songs alphabetically for the library sidebar
        sorted_songs = sorted(songs_data.keys())
        
        # We'll pass down a JSON mapping of song durations and bpms so the frontend JS can do instant math
        song_math_data = {}
        for song_name, info in songs_data.items():
            song_math_data[song_name] = {
                'duration': info.get('duration', 0),
                'bpm': info.get('bpm', 120),
                'has_horn': info.get('has_horn', False),
                'is_jam_vehicle': info.get('is_jam_vehicle', False),
                'energy': info.get('energy_level', 'standard')
            }
            
        return templates.TemplateResponse(request=request, name="builder/index.html", context={
            "request": request,
            "songs_data": songs_data,
            "sorted_songs": sorted_songs,
            "song_math_data": json.dumps(song_math_data),
            "active_page": "builder",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading builder: {str(e)}")


@router.post("/export", response_class=JSONResponse)
async def export_built_setlist(request: Request):
    """Receive built setlist JSON, save it to the mounted directory, and return a download link"""
    try:
        data = await request.json()
        
        venue = data.get('venue', 'New Show').strip()
        if not venue:
            venue = "Unknown Venue"
            
        date = data.get('date', datetime.now().strftime('%m/%d/%y')).strip()
        if not date:
            date = datetime.now().strftime('%m/%d/%y')
            
        sets = data.get('sets', {})
        # sets should look like: {'set1': [{'name': 'Song', 'bpm': 120}], 'set2': ...}
        
        # Construct the directory name format "Venue Setlist (MMDDYY)"
        # Note: if date is MM/DD/YY, strip the slashes for the directory name
        dir_date = date.replace('/', '')
        venue_dir_name = f"{venue} Setlist ({dir_date})"
        
        venue_dir = SETLISTS_DIR / venue_dir_name
        venue_dir.mkdir(parents=True, exist_ok=True)
        
        # File name is usually "Venue Date.md" or similar. We'll use "setlist.md" inside the venue dir
        # matching the existing structure where there's a markdown file inside the directory.
        file_name = f"{venue.replace(' ', '_')}_{dir_date}.md"
        file_path = venue_dir / file_name
        
        setlist_data = {
            'venue': venue,
            'date': date,
            'sets': sets,
            'file_path': str(file_path)
        }
        
        # Save it
        save_setlist_to_file(setlist_data)
        
        return {"success": True, "message": "Setlist saved successfully!"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})
