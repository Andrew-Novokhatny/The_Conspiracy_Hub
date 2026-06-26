"""
FastAPI server for band management app - refactored from Streamlit
Mobile-first design with HTMX for responsive, no-refresh experience
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
import os

# Initialize FastAPI app
app = FastAPI(
    title="Band Hub",
    description="Mobile-first band management app for The Conspiracy Hub",
    version="2.0.0"
)

# Configure CORS for local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local network access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup Jinja2 templates for HTMX
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Add custom template functions for mobile optimization
def mobile_friendly_duration(seconds: int) -> str:
    """Format duration in MM:SS for mobile display"""
    if not seconds or seconds <= 0:
        return "--:--"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def truncate_text(text: str, max_length: int = 30) -> str:
    """Truncate text for mobile displays"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

# Register template functions
templates.env.globals["mobile_duration"] = mobile_friendly_duration
templates.env.globals["truncate"] = truncate_text

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main application page - beautiful mobile-first design"""
    return templates.TemplateResponse(request=request, name="index.html", context={
        "request": request,
        "active_page": "home",
    })

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "ok", "app": "Band Hub", "version": "2.0.0"}

# Import API routers
from api import lyrics, songs, setlists, admin, builder

# Include API routes
app.include_router(lyrics.router, prefix="/api/lyrics", tags=["lyrics"])
app.include_router(songs.router, prefix="/api/songs", tags=["songs"])
app.include_router(setlists.router, prefix="/api/setlists", tags=["setlists"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(builder.router, prefix="/api/builder", tags=["builder"])

# Development server configuration
if __name__ == "__main__":
    import uvicorn

    # Get host and port from environment or use defaults
    host = os.getenv("BAND_APP_HOST", "0.0.0.0")  # Bind to all interfaces for Pi access
    port = int(os.getenv("BAND_APP_PORT", "8000"))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Enable for development
        access_log=True,
        log_level="info"
    )