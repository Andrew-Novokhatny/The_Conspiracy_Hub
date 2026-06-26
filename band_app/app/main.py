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
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>🎸 The Conspiracy Hub</title>
    <link rel="stylesheet" href="/static/css/band-theme.css">
    <script src="https://unpkg.com/htmx.org@1.9.6"></script>
    <style>
        .hero-gradient {
            background: radial-gradient(ellipse at center, rgba(30, 64, 175, 0.3) 0%, transparent 70%);
        }
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        }
    </style>
</head>
<body>
    <div class="hero-gradient">
        <div style="max-width: 1200px; margin: 0 auto; padding: 2rem 1rem;">

            <!-- Header -->
            <div style="text-align: center; margin-bottom: 3rem;" class="fade-in-up">
                <h1 class="band-title" style="font-size: 3rem; margin-bottom: 0.5rem;">🎸 The Conspiracy Hub</h1>
                <p class="text-muted" style="font-size: 1.1rem;">Mobile-optimized for musicians</p>
            </div>

            <!-- Stats Grid -->
            <div class="stats-grid fade-in-up" style="animation-delay: 0.2s;">
                <div class="stat-card">
                    <div class="stat-value">54</div>
                    <div class="stat-label">Songs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">48</div>
                    <div class="stat-label">Lyrics</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">12</div>
                    <div class="stat-label">Setlists</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">105</div>
                    <div class="stat-label">Avg BPM</div>
                </div>
            </div>

            <!-- Main Features -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 3rem;" class="fade-in-up" style="animation-delay: 0.4s;">

                <div class="band-card touch-target" onclick="window.location.href='/api/lyrics/1612'" style="cursor: pointer; text-align: center;">
                    <div class="feature-icon">📜</div>
                    <h3 class="section-title">Lyrics</h3>
                    <p class="text-muted" style="margin-bottom: 1.5rem;">View song lyrics with true full-screen mode optimized for mobile performance</p>
                    <div class="band-btn" style="display: inline-block;">Browse Lyrics</div>
                </div>

                <div class="band-card touch-target" onclick="window.location.href='/api/songs/list'" style="cursor: pointer; text-align: center;">
                    <div class="feature-icon">🎵</div>
                    <h3 class="section-title">Song Library</h3>
                    <p class="text-muted" style="margin-bottom: 1.5rem;">Browse 54 songs by BPM, energy level, horn sections, and jam vehicles</p>
                    <div class="band-btn" style="display: inline-block;">View Library</div>
                </div>

                <div class="band-card touch-target" onclick="window.location.href='/api/setlists/list'" style="cursor: pointer; text-align: center;">
                    <div class="feature-icon">📋</div>
                    <h3 class="section-title">Setlists</h3>
                    <p class="text-muted" style="margin-bottom: 1.5rem;">View previous shows, navigate through sets, and build new setlists</p>
                    <div class="band-btn" style="display: inline-block;">Browse Shows</div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div style="text-align: center; padding: 2rem 0;" class="fade-in-up" style="animation-delay: 0.6s;">
                <h3 class="section-title" style="margin-bottom: 2rem;">🚀 Quick Test</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center;">
                    <a href="/api/lyrics/1612/fullscreen" class="band-btn">Full-Screen Demo</a>
                    <a href="/api/songs/1612" class="band-btn-secondary">Song Details</a>
                    <a href="/health" class="band-btn-secondary">API Status</a>
                </div>
            </div>

            <!-- Footer -->
            <div style="text-align: center; padding-top: 3rem; border-top: 1px solid rgba(255,255,255,0.1);" class="fade-in-up" style="animation-delay: 0.8s;">
                <p class="text-muted" style="font-size: 0.9rem;">
                    ⚡ No page refreshes • 📱 Mobile-first • 🎸 Built for musicians
                </p>
            </div>

        </div>
    </div>
</body>
</html>""")

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "ok", "app": "Band Hub", "version": "2.0.0"}

# Import API routers
from api import lyrics, songs, setlists, admin

# Include API routes
app.include_router(lyrics.router, prefix="/api/lyrics", tags=["lyrics"])
app.include_router(songs.router, prefix="/api/songs", tags=["songs"])
app.include_router(setlists.router, prefix="/api/setlists", tags=["setlists"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

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