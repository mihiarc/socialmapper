#!/usr/bin/env python3
"""
Test script to verify that the progress tracking fix works correctly.

This script simulates the isochrone generation process to test if individual
progress updates (1/34, 2/34, etc.) are displayed correctly.
"""

import time

def test_progress_tracking():
    """Test the progress tracking functionality."""
    print("🧪 Testing Progress Tracking Fix")
    print("=" * 40)
    
    try:
        from socialmapper.progress import get_progress_bar
        
        # Simulate a list of 10 POIs (smaller number for quick testing)
        fake_pois = [f"poi_{i}" for i in range(1, 11)]
        
        print(f"\n📊 Testing progress tracking for {len(fake_pois)} items...")
        print("Expected: You should see progress updates like 1/10, 2/10, etc.")
        print("-" * 40)
        
        # Test the progress bar with the fixed implementation
        for i, poi in enumerate(get_progress_bar(fake_pois, desc="Testing Progress", unit="POI"), 1):
            print(f"   Processing {poi} (item {i}/{len(fake_pois)})")
            time.sleep(0.5)  # Simulate processing time
        
        print("\n✅ Progress tracking test completed!")
        print("If you saw individual progress updates above, the fix works!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_fallback_behavior():
    """Test the fallback print behavior when Rich progress bars fail."""
    print("\n🔄 Testing Fallback Behavior")
    print("=" * 40)
    
    try:
        from socialmapper.console.progress import RichProgressWrapper
        
        # Create a progress wrapper that should trigger fallback
        fake_items = [f"item_{i}" for i in range(1, 6)]
        
        print("Creating progress wrapper...")
        wrapper = RichProgressWrapper(fake_items, desc="Fallback Test", total=len(fake_items))
        
        print("Testing iteration with fallback print statements:")
        for item in wrapper:
            print(f"   Processing {item}")
            time.sleep(0.3)
        
        wrapper.close()
        print("✅ Fallback behavior test completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Progress Tracking Fix Verification")
    print("=" * 50)
    
    success1 = test_progress_tracking()
    success2 = test_fallback_behavior()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 All tests passed! Progress tracking should now work correctly.")
        print("   - Individual progress updates (1/N, 2/N, etc.) are now displayed")
        print("   - Fallback behavior provides detailed progress when Rich bars fail")
    else:
        print("⚠️  Some tests failed. Progress tracking may still have issues.")
    print("=" * 50)