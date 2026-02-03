# 🎸 Buckingham Conspiracy Hub

A Streamlit-based web application for managing band setlists, song libraries, and show archives for the Buckingham Conspiracy band.

## Features

- **📚 Song Library**: Manage the catalog in CSV (`songlist_master.csv`) with BPM, energy levels, and special markers
- **🎵 Setlist Builder**: Create and organize setlists with automatic timing calculations
- **📋 Previous Setlists**: Browse and edit historical setlists from past shows
- **📜 Lyrics Viewer**: Mobile/Desktop view modes with fullscreen toggle for performance use
- **🎸 Tabs & Notation**: View ASCII tabs, PDFs, and images (PDF tab viewer coming soon)
- **🗺️ Stage Plot**: View and download the latest stage plot PDF
- **🎛️ Mixer Configurations**: Upload/download mixer JSON configs and view mixer PDFs
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

Or bind-mount a single data directory:
```bash
./start.sh -d ~/buckingham_data
```

3. **Option B: Build and run manually**
```bash
# Build the image
docker build -t buckingham-conspiracy-hub .

# Recommended: bind-mount a single data directory
# (copy songlist/, setlists/, and song_data/ into ~/buckingham_data once)
mkdir -p ~/buckingham_data
cp -R songlist setlists song_data ~/buckingham_data/

docker run -d \
    --name buckingham-conspiracy-hub \
    -p 8501:8501 \
    -e BCH_DATA_DIR=/data \
    -v "$HOME/buckingham_data:/data" \
    --restart unless-stopped \
    buckingham-conspiracy-hub

# Alternative: mount individual directories
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
- **Build image**: `docker build -t buckingham-conspiracy-hub .`
- **Run container (bind-mount)**:
  `docker run -d --name buckingham-conspiracy-hub -p 8501:8501 -e BCH_DATA_DIR=/data -v "$HOME/buckingham_data:/data" --restart unless-stopped buckingham-conspiracy-hub`

### Deploying to a Raspberry Pi

1. **Build a Pi-ready image** (from the repo root):
    ```bash
    docker build -t buckingham-conspiracy-hub:pi-latest .
    docker images buckingham-conspiracy-hub:pi-latest
    ```
    Tagging with `pi-latest` (or a date) makes it easier to roll back later.

2. **Export the image to a tarball** so it can cross the network:
    ```bash
    docker save buckingham-conspiracy-hub:pi-latest | gzip > /tmp/buckingham-conspiracy-hub.tar.gz
    ```

3. **Copy the tarball to your Raspberry Pi** (replace `<pi-host>` with your Pi’s hostname or IP):
    ```bash
    scp /tmp/buckingham-conspiracy-hub.tar.gz pi@<pi-host>:/tmp/
    mkdir -p ~/buckingham_data
    rsync -a songlist setlists song_data mixer_configurations stage_plots pi@<pi-host>:~/buckingham_data/
    ```
    The `rsync` step only needs to run once unless the data changes.

4. **Load and restart the container on the Pi**:
    ```bash
    ssh pi@<pi-host> <<'EOF'
    docker load < /tmp/buckingham-conspiracy-hub.tar.gz
    docker stop buckingham-conspiracy-hub || true
    docker rm buckingham-conspiracy-hub || true
    docker run -d \
        --name buckingham-conspiracy-hub \
        -p 8501:8501 \
        -e BCH_DATA_DIR=/data \
        -v ~/buckingham_data:/data \
        --restart unless-stopped \
        buckingham-conspiracy-hub:pi-latest
    EOF
    ```
    That command reuses the same port and data layout as the desktop instructions. Update `~/buckingham_data` if you keep the files elsewhere.

5. **Verify the Pi container** with `ssh pi@<pi-host> docker ps` and `docker logs -f buckingham-conspiracy-hub`.

If your Pi is air-gapped, you can skip `rsync` and ship the `songlist/`, `setlists/`, and `song_data/` folders on a thumb drive, then populate `~/buckingham_data` before running the container.

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
README.md
buckingham_conspiracy/
├── src/
│   ├── __init__.py
│   └── app.py              # Main Streamlit application
├── setlists/               # Historical setlist storage
├── songlist/               # Song library data (CSV master)
│   └── songlist_master.csv
├── song_data/              # Lyrics + tabs
├── mixer_configurations/   # Mixer JSON + PDF references
├── stage_plots/            # Stage plot PDFs
├── requirements.txt        # Python dependencies
└── Dockerfile             # Docker container configuration
```

## Data Persistence

When running with Docker, bind-mount your data directory so edits persist between container restarts. The recommended approach is to mount a single directory and set `BCH_DATA_DIR` (see the Docker section above). Include `songlist/`, `setlists/`, `song_data/`, `mixer_configurations/`, and `stage_plots/` under that data root.

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

The application uses relative paths by default. To store data outside the repo, set `BCH_DATA_DIR` (or `DATA_DIR`) to a bind-mounted directory that contains `songlist/`, `setlists/`, `song_data/`, `mixer_configurations/`, and `stage_plots/`.

## Legend

- 🎺 = Horn parts
- 🥁 = Drum Vocal parts
- 🛸 = Jam vehicle
- 🔥 = High energy
- 💤 = Low energy

## Support

For issues or questions, please open an issue in the repository.
