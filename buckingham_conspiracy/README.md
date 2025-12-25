# 🎸 Buckingham Conspiracy Hub

A Streamlit-based web application for managing band setlists, song libraries, and show archives for the Buckingham Conspiracy band.

## Features

- **📚 Song Library**: Manage and edit your complete song catalog with BPM, energy levels, and special markers
- **🎵 Setlist Builder**: Create and organize setlists with automatic timing calculations
- **📋 Previous Setlists**: Browse and edit historical setlists from past shows
- **📜 Lyrics Viewer**: View song lyrics with device-optimized display modes (Mobile/Tablet/Desktop) for rehearsals and performances
- **🎺 Special Markers**: Track horn parts, vocal parts, jam vehicles, and energy levels

## Quick Start with Docker

### Prerequisites
- Docker installed on your system

### Running the Application

1. Navigate to the buckingham_conspiracy directory:
```bash
cd buckingham_conspiracy
```

2. **Option A: Use the startup script (easiest)**
```bash
./start.sh
```

Or specify a custom port:
```bash
./start.sh -p 8080
```

3. **Option B: Build and run manually**
```bash
# Build the image
docker build -t buckingham-conspiracy-hub .

# Run the container (default port 8501)
docker run -d \
    --name buckingham-conspiracy-hub \
    -p 8501:8501 \
    -v "$(pwd)/setlists:/app/setlists" \
    -v "$(pwd)/songlist:/app/songlist" \
    -v "$(pwd)/song_data:/app/song_data" \
    --restart unless-stopped \
    buckingham-conspiracy-hub

# Or use a custom port (e.g., 8080)
docker run -d \
    --name buckingham-conspiracy-hub \
    -p 8080:8501 \
    -v "$(pwd)/setlists:/app/setlists" \
    -v "$(pwd)/songlist:/app/songlist" \
    -v "$(pwd)/song_data:/app/song_data" \
    --restart unless-stopped \
    buckingham-conspiracy-hub
```

4. Access the application at: `http://localhost:8502` when using `start.sh` (the script maps the container’s 8501 to 8502 by default) or `http://localhost:8501` when you run the container manually as shown above.

### Docker Commands

- **View logs**: `docker logs -f buckingham-conspiracy-hub`
- **Stop app**: `docker stop buckingham-conspiracy-hub`
- **Start stopped container**: `docker start buckingham-conspiracy-hub`
- **Restart**: `docker restart buckingham-conspiracy-hub`
- **Remove container**: `docker rm buckingham-conspiracy-hub`
- **Rebuild image**: `docker build -t buckingham-conspiracy-hub .`

## Local Development (without Docker)

### Prerequisites
- Python 3.11 or higher
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run src/app.py
```

3. Access the application at: `http://localhost:8501`

## Project Structure

```
buckingham_conspiracy/
├── src/
│   ├── __init__.py
│   └── app.py              # Main Streamlit application
├── setlists/               # Historical setlist storage
├── songlist/               # Song library data
├── song_data/              # Lyrics files (.txt format)
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container configuration
└── README.md             # This file
```

## Data Persistence

When running with Docker, the `setlists`, `songlist`, and `song_data` directories are mounted as volumes, ensuring your data persists between container restarts.

### Adding Lyrics

To add lyrics for songs:
1. Create a `.txt` file in the `song_data/` directory
2. Name it with the song title (e.g., `Move.txt`)
3. Add the lyrics line by line
4. The lyrics will automatically appear in the Lyrics tab

### Optional: Populate Lyrics with the Genius API

The helper script at `scripts/genius_fetch_lyrics.py` can automate lyric collection by:
1. Querying the Genius search API for each song (title + artist)
2. Opening the Genius song page returned by the API
3. Scraping the rendered HTML lyrics containers and saving the text into `song_data/lyrics`

To use it:
1. [Create a Genius API client](https://docs.genius.com/) for this project. When the form asks for an app website, you can use the repo URL (`https://github.com/Andrew-Novokhatny/The_Conspiracy_Hub`).
2. Export the token (or pass it via `--token`):
    ```bash
    export GENIUS_ACCESS_TOKEN="<your-token>"
    ```
3. Install dependencies if you have not already:
    ```bash
    pip install -r requirements.txt
    ```
4. Run the script from the repo root.
    - Fetch one song: `python scripts/genius_fetch_lyrics.py --song "1612"`
    - Fill gaps (first 5 missing files): `python scripts/genius_fetch_lyrics.py --all-missing --limit 5`
    - Rebuild every file: add `--overwrite`

Respect Genius’s API terms of service and rate limits, and ensure you are licensed to store any lyrics you download.

## Configuration

The application uses relative paths, making it portable across different environments. No configuration changes needed for basic usage.

## Legend

- 🎺 = Horn parts
- 🥁 = Drum Vocal parts
- 🛸 = Jam vehicle
- 🔥 = High energy
- 💤 = Low energy

## Support

For issues or questions, please open an issue in the repository.
