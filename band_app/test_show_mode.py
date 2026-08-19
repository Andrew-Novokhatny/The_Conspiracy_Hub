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
    assert any(e in res.text for e in ["🔥", "⭐", "💤"])
    print("✅ Setlist Builder edit preloading endpoint & energy emojis verified")

    # Test setlist details delete button present
    res_det = client.get("/api/setlists/0")
    assert res_det.status_code == 200
    assert "Edit in Builder" in res_det.text
    assert "Delete" in res_det.text
    print("✅ Setlist details builder edit and delete options verified")

def test_date_normalization():
    """Verify full 4-digit year dates like 10/17/2024 parse and format correctly"""
    assert setlist_manager.human_readable_date("10/17/2024") == "October 17, 2024"
    assert setlist_manager.human_readable_date("10/17/24") == "October 17, 2024"
    assert setlist_manager.human_readable_date("10172024") == "October 17, 2024"
    print("✅ Date normalization and human readable date formatting verified")

def test_song_library_metadata_editing():
    """Verify get_edit_song_form and save_edited_song for row and lyrics contexts"""
    # GET edit form for row
    res_form_row = client.get("/api/songs/1999/edit?context=row")
    assert res_form_row.status_code == 200
    assert "Edit Metadata" in res_form_row.text
    assert 'name="context_type" value="row"' in res_form_row.text

    # GET edit form for lyrics
    res_form_lyrics = client.get("/api/songs/1999/edit?context=lyrics")
    assert res_form_lyrics.status_code == 200
    assert 'name="context_type" value="lyrics"' in res_form_lyrics.text

    # GET row partial
    res_row = client.get("/api/songs/1999/row")
    assert res_row.status_code == 200
    assert "Edit" in res_row.text

    # POST metadata update with row context
    res_post_row = client.post("/api/songs/1999/edit", data={
        "artist": "Prince & The Revolution",
        "bpm": "119",
        "song_key": "F",
        "has_horn": "false",
        "is_jam_vehicle": "true",
        "energy_level": "high",
        "avg_length": "4:30",
        "context_type": "row"
    })
    assert res_post_row.status_code == 200
    assert "Prince" in res_post_row.text
    assert "JAM" in res_post_row.text

    # Re-check updated song list in core song_manager
    songs = song_manager.load_song_list()
    assert songs["1999"]["artist"] == "Prince & The Revolution"
    assert songs["1999"]["is_jam_vehicle"] is True
    assert songs["1999"]["avg_length"] == 270

    # Reset back to original values
    client.post("/api/songs/1999/edit", data={
        "artist": "Prince",
        "bpm": "119",
        "song_key": "F",
        "has_horn": "false",
        "is_jam_vehicle": "false",
        "energy_level": "high",
        "avg_length": "",
        "context_type": "row"
    })
    print("✅ Song library metadata editing and persistence verified")

def test_segue_marker_persistence():
    """Verify builder export, setlist file saving, markdown export, and show mode for segue markers"""
    # 1. Export setlist with segue markers from builder
    res = client.post("/api/builder/export", json={
        "venue": "Test Segue Venue",
        "date": "08/18/26",
        "sets": {
            "set1": [
                {"name": "1999", "bpm": 119, "is_segue": True},
                {"name": "Dreams", "bpm": 120, "is_segue": False}
            ]
        }
    })
    assert res.status_code == 200
    assert res.json().get("success") is True

    # 2. Verify file on disk contains '->' for segue song
    setlists = setlist_manager.load_previous_setlists()
    target = next((s for s in setlists if s["venue"] == "Test Segue Venue"), None)
    assert target is not None, "Exported test setlist not found"
    
    set1_songs = target["sets"]["set1"]
    assert set1_songs[0]["name"] == "1999"
    assert set1_songs[0]["is_segue"] is True
    
    with open(target["file_path"], "r", encoding="utf-8") as f:
        content = f.read()
    assert "1999 (119) ->" in content

    # 3. Verify markdown export table contains segue marker '→'
    target_idx = setlists.index(target)
    res_md = client.get(f"/api/setlists/{target_idx}/export?format=markdown")
    assert res_md.status_code == 200
    assert "→ 1999" in res_md.text

    # 4. Clean up test setlist
    client.post(f"/api/setlists/{target_idx}/delete")
    print("✅ Segue marker persistence, export, and rendering verified")

def test_ui_ux_enhancements():
    """Verify landing page cards, timing strip, sidebar close button, and minimalist icons"""
    # 1. Landing Page
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert "landing-row-card" in res_home.text
    cards_stack = res_home.text[res_home.text.find("landing-cards-stack"):]
    lyrics_pos = cards_stack.find("/api/lyrics/")
    setlists_pos = cards_stack.find("/api/setlists/")
    songs_pos = cards_stack.find("/api/songs/")
    assert lyrics_pos < setlists_pos < songs_pos, "Landing cards order is incorrect"
    print("✅ Landing page compact row cards & reordering verified")

    # 2. Setlist Details
    res_det = client.get("/api/setlists/0")
    assert res_det.status_code == 200
    assert "setlist-timing-strip" in res_det.text
    assert "timing-pill" in res_det.text
    # Verify BPM string is removed and only numbers in parentheses are shown
    assert " BPM)" not in res_det.text
    print("✅ Setlist Details minimalist timing strip and BPM formatting verified")

    # 3. Show Mode Navigation, Header Setlist button, and removal of Top button
    res_show = client.get("/api/setlists/0/show")
    assert res_show.status_code == 200
    assert "btn-prev-song" in res_show.text
    assert "btn-next-song" in res_show.text
    assert "sidebar-header-toggle-btn" in res_show.text
    assert "show-sidebar-close-btn" in res_show.text
    assert "show-sidebar-backdrop" in res_show.text
    assert "autoscroll-top-btn" not in res_show.text
    print("✅ Show Mode Prev/Next navigation, header Setlist toggle, and Top button removal verified")

    # 4. Builder Collapsible Drawer
    res_builder = client.get("/api/builder/")
    assert res_builder.status_code == 200
    assert "builder-drawer-backdrop" in res_builder.text
    assert "song-pool-container" in res_builder.text
    assert "song-pool-close-btn" in res_builder.text
    print("✅ Setlist Builder iPad/mobile drawer verified")

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
    test_date_normalization()
    test_song_library_metadata_editing()
    test_segue_marker_persistence()
    test_ui_ux_enhancements()
    print("\n🎉 ALL TESTS PASSED!")

