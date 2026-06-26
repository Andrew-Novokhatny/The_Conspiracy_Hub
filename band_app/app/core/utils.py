"""Utility functions for band app - extracted from Streamlit app."""

import base64
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Union

from .song_manager import DATA_ROOT, BASE_DIR


# Data paths
SONG_DATA_DIR = DATA_ROOT / "buckingham_conspiracy" / "song_data"
TABS_DIR = SONG_DATA_DIR / "tabs"
MIXER_CONFIG_DIR = DATA_ROOT / "buckingham_conspiracy" / "mixer_configurations"
STAGE_PLOTS_DIR = DATA_ROOT / "buckingham_conspiracy" / "stage_plots"

# File extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"}
DOCUMENT_EXTENSIONS = {".pdf"}
TAB_UPLOAD_TYPES = [ext.lstrip(".") for ext in sorted(IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS)]


def describe_data_path(path: Path) -> str:
    """Get a user-friendly description of a data path."""
    for root in (DATA_ROOT, BASE_DIR):
        try:
            return str(path.relative_to(root))
        except ValueError:
            continue
    return str(path)


def list_files_by_extension(directory: Path, extensions: tuple[str, ...]) -> List[Path]:
    """List files in a directory with specific extensions."""
    if not directory.exists():
        return []
    normalized = {ext.lower() for ext in extensions}
    files = [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in normalized]
    return sorted(files, key=lambda p: p.name.lower())


def render_pdf_as_data_uri(file_path: Path) -> Optional[str]:
    """Render a PDF as a data URI for iframe embedding."""
    if not file_path.exists():
        return None
    try:
        pdf_bytes = file_path.read_bytes()
        encoded = base64.b64encode(pdf_bytes).decode("ascii")
        return f"data:application/pdf;base64,{encoded}"
    except Exception:
        return None


def sanitize_tab_filename(filename: str) -> str:
    """Sanitize a tab filename for safe storage."""
    base = Path(filename).stem
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).strip("_-")
    if not sanitized:
        sanitized = "tab_upload"
    return sanitized


def save_uploaded_tab(file_bytes: bytes, original_filename: str) -> Optional[Path]:
    """Save uploaded tab file to the tabs directory."""
    ext = Path(original_filename).suffix.lower()
    if ext not in IMAGE_EXTENSIONS and ext not in DOCUMENT_EXTENSIONS:
        raise ValueError("Only PDF or common image files are supported for tab uploads.")

    TABS_DIR.mkdir(parents=True, exist_ok=True)
    sanitized_name = sanitize_tab_filename(original_filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    destination = TABS_DIR / f"{sanitized_name}_{timestamp}{ext}"

    try:
        with open(destination, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        raise Exception(f"Failed to save uploaded tab: {e}")

    return destination


def load_available_tabs() -> List[str]:
    """Load list of available tab files"""
    try:
        tab_files: set[str] = set()
        if TABS_DIR.exists():
            for file in TABS_DIR.glob("*"):
                if file.is_file():
                    tab_files.add(file.name)
        return sorted(tab_files)
    except Exception as e:
        raise Exception(f"Error loading tab files: {e}")


def resolve_tab_file(filename: str) -> Optional[Path]:
    """Find the actual path for a tab filename across supported directories"""
    search_paths = [TABS_DIR]
    for directory in search_paths:
        if not directory.exists():
            continue
        candidate = directory / filename
        if candidate.exists():
            return candidate
    return None


def load_tab_content(filename: str) -> Tuple[Union[str, dict], str]:
    """Load tab content from file. Returns (content, file_type)"""
    try:
        tab_file = resolve_tab_file(filename)
        if tab_file is None:
            return f"Tab file '{filename}' not found.", 'error'

        file_ext = tab_file.suffix.lower()
        if file_ext in ['.txt', '.tab']:
            with open(tab_file, 'r', encoding='utf-8') as f:
                return f.read(), 'text'
        elif file_ext == '.pdf':
            return {'file_path': str(tab_file)}, 'pdf'
        elif file_ext in IMAGE_EXTENSIONS:
            return {'file_path': str(tab_file)}, 'image'
        else:
            return f"Unsupported tab file format: {file_ext}", 'error'
    except Exception as e:
        return f"Error loading tab: {e}", 'error'


def load_mixer_configurations() -> List[Path]:
    """Load available mixer configuration files."""
    if not MIXER_CONFIG_DIR.exists():
        return []
    return list_files_by_extension(MIXER_CONFIG_DIR, ('.json',))


def load_stage_plots() -> List[Path]:
    """Load available stage plot files."""
    if not STAGE_PLOTS_DIR.exists():
        return []
    return list_files_by_extension(STAGE_PLOTS_DIR, ('.pdf', '.png', '.jpg', '.jpeg'))


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    if not file_path.exists():
        return 0.0
    return file_path.stat().st_size / (1024 * 1024)


def ensure_directory_exists(path: Path) -> bool:
    """Ensure a directory exists, create it if it doesn't."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False