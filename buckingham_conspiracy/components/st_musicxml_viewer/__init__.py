import streamlit.components.v1 as components
import os
from pathlib import Path

# Get the build directory
_build_dir = Path(__file__).resolve().parent / "frontend" / "build"

# Declare the component
st_musicxml_viewer = components.declare_component(
    "st_musicxml_viewer",
    path=str(_build_dir)
)

def musicxml_viewer(musicxml_file_path: str, key: str = None):
    """
    Renders a MusicXML file using OpenSheetMusicDisplay.

    :param musicxml_file_path: The absolute path to the MusicXML file.
    :param key: An optional key for the component.
    """
    try:
        with open(musicxml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        component_value = st_musicxml_viewer(xml_content=xml_content, key=key)
        return component_value
    except FileNotFoundError:
        return f"Error: File not found at {musicxml_file_path}"
    except Exception as e:
        return f"An error occurred: {e}"
