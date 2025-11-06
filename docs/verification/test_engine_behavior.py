"""
Test FarmTractor engine behavior
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from afs_fastapi.equipment.farm_tractors import FarmTractor


def test_engine_behavior():
    """Test engine behavior details."""
    print("=== FarmTractor Engine Behavior Test ===")

    try:
        tractor = FarmTractor("John Deere", "8RX", 2023)

        print("Initial state:")
        print(f"  Engine on: {tractor.engine_on}")
        print(f"  Engine RPM: {tractor.engine_rpm}")
        print(f"  Speed: {tractor.speed}")

        result = tractor.start_engine()
        print("\nAfter start_engine():")
        print(f"  Result: {result}")
        print(f"  Engine on: {tractor.engine_on}")
        print(f"  Engine RPM: {tractor.engine_rpm}")
        print(f"  Speed: {tractor.speed}")

        # Try to accelerate to see if RPM changes
        result = tractor.accelerate(5)
        print("\nAfter accelerate(5):")
        print(f"  Result: {result}")
        print(f"  Engine on: {tractor.engine_on}")
        print(f"  Engine RPM: {tractor.engine_rpm}")
        print(f"  Speed: {tractor.speed}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_engine_behavior()