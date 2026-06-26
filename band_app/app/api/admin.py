"""Admin API endpoints for running Python scripts and maintenance tasks"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import subprocess
import sys
from pathlib import Path

router = APIRouter()

# Path to original scripts
SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "buckingham_conspiracy" / "scripts"

@router.post("/fetch-lyrics/{song_name}")
async def fetch_lyrics_for_song(song_name: str, background_tasks: BackgroundTasks):
    """Fetch lyrics for a specific song using the original script"""
    try:
        script_path = SCRIPTS_DIR / "fetch_lyrics.py"
        if not script_path.exists():
            raise HTTPException(status_code=404, detail="fetch_lyrics.py script not found")

        # Add background task to run script
        background_tasks.add_task(run_fetch_lyrics_script, song_name)

        return {
            "status": "started",
            "message": f"Lyrics fetch started for '{song_name}'",
            "song_name": song_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting lyrics fetch: {str(e)}")

@router.post("/update-artists")
async def update_artists_database(background_tasks: BackgroundTasks):
    """Update the artists database using the original script"""
    try:
        script_path = SCRIPTS_DIR / "update_artists.py"
        if not script_path.exists():
            raise HTTPException(status_code=404, detail="update_artists.py script not found")

        # Add background task to run script
        background_tasks.add_task(run_update_artists_script)

        return {
            "status": "started",
            "message": "Artists database update started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting artists update: {str(e)}")

async def run_fetch_lyrics_script(song_name: str):
    """Background task to run fetch lyrics script"""
    try:
        script_path = SCRIPTS_DIR / "fetch_lyrics.py"
        result = subprocess.run([
            sys.executable, str(script_path), song_name
        ], capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            print(f"Fetch lyrics script failed: {result.stderr}")
        else:
            print(f"Fetch lyrics completed for {song_name}: {result.stdout}")

    except subprocess.TimeoutExpired:
        print(f"Fetch lyrics script timed out for {song_name}")
    except Exception as e:
        print(f"Error running fetch lyrics script: {e}")

async def run_update_artists_script():
    """Background task to run update artists script"""
    try:
        script_path = SCRIPTS_DIR / "update_artists.py"
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            print(f"Update artists script failed: {result.stderr}")
        else:
            print(f"Update artists completed: {result.stdout}")

    except subprocess.TimeoutExpired:
        print("Update artists script timed out")
    except Exception as e:
        print(f"Error running update artists script: {e}")

@router.get("/scripts/status")
async def get_scripts_status():
    """Check if admin scripts are available"""
    scripts_status = {}

    for script_name in ["fetch_lyrics.py", "update_artists.py"]:
        script_path = SCRIPTS_DIR / script_name
        scripts_status[script_name] = {
            "exists": script_path.exists(),
            "path": str(script_path)
        }

    return {
        "scripts_directory": str(SCRIPTS_DIR),
        "scripts": scripts_status
    }