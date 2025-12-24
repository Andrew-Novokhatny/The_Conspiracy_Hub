# 🎸 Buckingham Conspiracy Hub

A Streamlit-based web application for managing band setlists, song libraries, and show archives for the Buckingham Conspiracy band.

## Features

- **📚 Song Library**: Manage and edit your complete song catalog with BPM, energy levels, and special markers
- **🎵 Setlist Builder**: Create and organize setlists with automatic timing calculations
- **📋 Previous Setlists**: Browse and edit historical setlists from past shows
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
    --restart unless-stopped \
    buckingham-conspiracy-hub

# Or use a custom port (e.g., 8080)
docker run -d \
    --name buckingham-conspiracy-hub \
    -p 8080:8501 \
    -v "$(pwd)/setlists:/app/setlists" \
    -v "$(pwd)/songlist:/app/songlist" \
    --restart unless-stopped \
    buckingham-conspiracy-hub
```

4. Access the application at: `http://localhost:8501` (or your custom port)

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
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container configuration
├── docker-compose.yml     # Docker Compose orchestration
└── README.md             # This file
```

## Data Persistence

When running with Docker, the `setlists` and `songlist` directories are mounted as volumes, ensuring your data persists between container restarts.

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
