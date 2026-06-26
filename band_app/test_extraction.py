#!/usr/bin/env python3
"""
Test script to verify extracted business logic modules work correctly
without Streamlit dependency.
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

def test_imports():
    """Test that all modules can be imported without errors."""
    print("Testing imports...")

    try:
        from core import song_manager, lyrics_manager, setlist_manager, utils
        print("✅ All core modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_song_manager():
    """Test song management functionality."""
    print("\nTesting song manager...")

    try:
        from core import song_manager

        # Test utility functions
        result = song_manager.parse_bool("true")
        assert result == True, "parse_bool failed"

        result = song_manager.parse_bool("false")
        assert result == False, "parse_bool failed"

        # Test duration calculation
        duration = song_manager.calculate_song_duration(120)
        assert duration > 0, "duration calculation failed"

        # Test CSV headers
        assert len(song_manager.SONGLIST_CSV_HEADERS) == 7, "CSV headers incorrect"

        print("✅ Song manager basic functions work")

        # Try to load song list if data exists
        try:
            songs = song_manager.load_song_list()
            print(f"✅ Loaded {len(songs)} songs from data files")

            if songs:
                stats = song_manager.get_song_stats(songs)
                print(f"✅ Song stats: {stats['total_songs']} total, {stats['avg_bpm']} avg BPM")
        except Exception as e:
            print(f"⚠️  Could not load song data (expected if data files don't exist): {e}")

        return True

    except Exception as e:
        print(f"❌ Song manager test failed: {e}")
        return False

def test_lyrics_manager():
    """Test lyrics management functionality."""
    print("\nTesting lyrics manager...")

    try:
        from core import lyrics_manager

        # Test format function
        test_lyrics = "[Verse 1]\nThis is a test\n[Chorus]\nTest chorus"
        formatted = lyrics_manager.format_lyrics_for_display(test_lyrics)
        assert "strong" in formatted, "Lyrics formatting failed"

        print("✅ Lyrics formatting works")

        # Try to load lyrics if data exists
        try:
            lyrics_list = lyrics_manager.load_available_lyrics()
            print(f"✅ Found {len(lyrics_list)} lyrics files")

            if lyrics_list:
                # Test loading content of first lyrics file
                content = lyrics_manager.load_lyrics_content(lyrics_list[0])
                print(f"✅ Loaded lyrics content ({len(content)} characters)")
        except Exception as e:
            print(f"⚠️  Could not load lyrics data (expected if data files don't exist): {e}")

        return True

    except Exception as e:
        print(f"❌ Lyrics manager test failed: {e}")
        return False

def test_setlist_manager():
    """Test setlist management functionality."""
    print("\nTesting setlist manager...")

    try:
        from core import setlist_manager

        # Test utility functions
        duration_str = setlist_manager.format_duration(125)
        assert duration_str == "02:05", f"Duration format failed: got {duration_str}"

        emoji = setlist_manager.get_energy_emoji("high")
        assert emoji == "🔥", "Energy emoji failed"

        options = setlist_manager.get_energy_options()
        assert len(options) == 3, "Energy options failed"

        print("✅ Setlist manager basic functions work")

        # Try to load setlists if data exists
        try:
            setlists = setlist_manager.load_previous_setlists()
            print(f"✅ Loaded {len(setlists)} previous setlists")
        except Exception as e:
            print(f"⚠️  Could not load setlist data (expected if data files don't exist): {e}")

        return True

    except Exception as e:
        print(f"❌ Setlist manager test failed: {e}")
        return False

def test_utils():
    """Test utility functions."""
    print("\nTesting utils...")

    try:
        from core import utils

        # Test filename sanitization
        sanitized = utils.sanitize_tab_filename("My Song! (Version 2).pdf")
        assert "_" in sanitized or sanitized.isalnum(), f"Sanitization failed: {sanitized}"

        # Test path description
        test_path = Path("/some/test/path")
        desc = utils.describe_data_path(test_path)
        assert isinstance(desc, str), "Path description failed"

        print("✅ Utils basic functions work")

        # Try to load tabs if data exists
        try:
            tabs = utils.load_available_tabs()
            print(f"✅ Found {len(tabs)} tab files")
        except Exception as e:
            print(f"⚠️  Could not load tab data (expected if data files don't exist): {e}")

        return True

    except Exception as e:
        print(f"❌ Utils test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🎸 Testing extracted business logic modules\n")

    tests = [
        test_imports,
        test_song_manager,
        test_lyrics_manager,
        test_setlist_manager,
        test_utils
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Business logic extraction successful.")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)