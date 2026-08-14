#!/usr/bin/env python3
"""Comprehensive test for new songs, Show Mode, and autoscroll integration"""

import sys
from pathlib import Path
from starlette.testclient import TestClient

# Add app directory to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

import main
from core import song_manager, lyrics_manager, setlist_manager

client = TestClient(main.app)

def test_new_songs_in_song_list():
    """Verify that 1999, Abracadabra, Rock With You, and It Ain't Over Till It's Over are in songlist"""
    songs = song_manager.load_song_list()
    
    expected_new_songs = [
        ("1999", "Prince", 119),
        ("Abracadabra", "Steve Miller Band", 127),
        ("Rock With You", "Michael Jackson", 114),
        ("It Ain't Over Till It's Over", "Lenny Kravitz", 80),
    ]

    for title, artist, bpm in expected_new_songs:
        assert title in songs, f"Song '{title}' not found in songlist"
        assert songs[title]["artist"] == artist, f"Artist for '{title}' mismatch: got {songs[title]['artist']}, expected {artist}"
        assert songs[title]["bpm"] == bpm, f"BPM for '{title}' mismatch: got {songs[title]['bpm']}, expected {bpm}"
    
    print(f"✅ All 4 new songs verified in song catalog ({len(songs)} total songs)")

def test_lyrics_loaded():
    """Verify lyrics exist for all new songs"""
    new_songs = [
        "1999",
        "Abracadabra",
        "Rock With You",
        "It Ain't Over Till It's Over",
        "Dreams",
        "Crosseyed and Painless",
        "Everybody Wants to Rule the World"
    ]

    for song in new_songs:
        content = lyrics_manager.load_lyrics_content(song)
        assert "not found" not in content.lower() and len(content.strip()) > 20, f"Lyrics for '{song}' failed to load"
    
    print("✅ All lyrics verified and accessible")

def test_show_mode_endpoint():
    """Test /api/setlists/{setlist_id}/show full page and HTMX partial"""
    # Test setlist 0
    res = client.get("/api/setlists/0/show")
    assert res.status_code == 200
    assert "Show Mode" in res.text
    assert "autoscroll.js" in res.text
    assert "show-bottom-bar" in res.text
    assert "show-sidebar" in res.text
    print("✅ Show Mode full page endpoint rendered successfully")

    # Test HTMX partial
    res_partial = client.get("/api/setlists/0/show?song=1&partial=1", headers={"HX-Request": "true"})
    assert res_partial.status_code == 200
    assert "show-song-hero" in res_partial.text
    assert "show-lyrics-container" in res_partial.text
    print("✅ Show Mode HTMX partial endpoint rendered successfully")

def test_fullscreen_lyrics_with_autoscroll():
    """Test /api/lyrics/{song_name}/fullscreen includes autoscroll"""
    res = client.get("/api/lyrics/1999/fullscreen")
    assert res.status_code == 200
    assert "lyrics-floating-autoscroll" in res.text
    assert "autoscroll.js" in res.text
    assert "1999" in res.text
    print("✅ Fullscreen lyrics autoscroll endpoint verified")

def test_regular_lyrics_with_autoscroll():
    """Test /api/lyrics/{song_name} includes autoscroll controls"""
    res = client.get("/api/lyrics/1999")
    assert res.status_code == 200
    assert "autoscroll-bar" in res.text
def test_song_key_metadata():
    """Test song key editing, saving, builder, lyrics and show mode rendering"""
    # 1. Edit song key for '1999' via POST
    res = client.post("/api/songs/1999/edit", data={
        "artist": "Prince",
        "bpm": "119",
        "song_key": "F",
        "has_horn": "false",
        "is_jam_vehicle": "false",
        "energy_level": "high"
    })
    assert res.status_code == 200
    assert "F" in res.text
    assert "Key" in res.text
    print("✅ Song Key edit and save POST verified")

    # 2. Check song details API returns song_key
    res_details = client.get("/api/songs/1999")
    assert res_details.status_code == 200
    data = res_details.json()
    assert data.get("song_key") == "F"
    print("✅ Song details API returns song_key")

    # 3. Check lyrics view includes song key
    res_lyrics = client.get("/api/lyrics/1999")
    assert res_lyrics.status_code == 200
    assert "Key: F" in res_lyrics.text
    print("✅ Lyrics view renders song_key")

def test_dont_you_forget_about_me():
    """Verify Don't You (Forget About Me) in songlist & lyrics"""
    songs = song_manager.load_song_list()
    assert "Don't You (Forget About Me)" in songs
    assert songs["Don't You (Forget About Me)"]["artist"] == "Simple Minds"
    
    lyrics = lyrics_manager.load_lyrics_content("Don't You (Forget About Me)")
    assert "forget about me" in lyrics.lower()
    print("✅ Don't You (Forget About Me) song catalog & lyrics verified")

def test_builder_edit_and_delete_setlist():
    """Test loading an existing setlist in builder and delete function"""
    # Test builder edit preloading
    res = client.get("/api/builder/?edit=0")
    assert res.status_code == 200
    assert "initialSetlist" in res.text
    print("✅ Setlist Builder edit preloading endpoint verified")

    # Test setlist details delete button present
    res_det = client.get("/api/setlists/0")
    assert res_det.status_code == 200
    assert "Edit in Builder" in res_det.text
    assert "Delete" in res_det.text
    print("✅ Setlist details builder edit and delete options verified")

if __name__ == "__main__":
    print("🎸 Running Show Mode, Autoscroll, Builder Edit & Delete Tests...\n")
    test_new_songs_in_song_list()
    test_dont_you_forget_about_me()
    test_lyrics_loaded()
    test_show_mode_endpoint()
    test_fullscreen_lyrics_with_autoscroll()
    test_regular_lyrics_with_autoscroll()
    test_song_key_metadata()
    test_builder_edit_and_delete_setlist()
    print("\n🎉 ALL TESTS PASSED!")

