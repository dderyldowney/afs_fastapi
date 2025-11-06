"""
Investigate FarmTractor attribute structure
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from afs_fastapi.equipment.farm_tractors import FarmTractor


def investigate_farm_tractor():
    """Investigate FarmTractor attribute structure."""
    print("=== FarmTractor Attribute Investigation ===")

    try:
        tractor = FarmTractor("John Deere", "8RX", 2023)

        # Check all attributes
        print(f"FarmTractor attributes: {vars(tractor)}")

        # Test hydraulics specifically
        print(f"Initial hydraulics: {tractor.hydraulics} (type: {type(tractor.hydraulics)})")

        result = tractor.activate_hydraulics()
        print(f"After activate: {tractor.hydraulics} (type: {type(tractor.hydraulics)})")
        print(f"Activate result: {result}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    investigate_farm_tractor()