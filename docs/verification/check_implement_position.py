"""
Check FarmTractor implement position values
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from afs_fastapi.equipment.farm_tractors import FarmTractor

def check_implement_position():
    """Check implement position enum values."""
    print("=== FarmTractor Implement Position Check ===")

    try:
        tractor = FarmTractor("John Deere", "8RX", 2023)
        tractor.start_engine()
        tractor.activate_hydraulics()

        print(f"Initial implement position: {tractor.implement_position}")
        print(f"Initial implement position (str): {str(tractor.implement_position)}")
        print(f"Initial implement position (repr): {repr(tractor.implement_position)}")

        result = tractor.lower_implement()
        print(f"\nAfter lower_implement(): {result}")
        print(f"Implement position: {tractor.implement_position}")
        print(f"Implement position (str): {str(tractor.implement_position)}")
        print(f"Implement position (repr): {repr(tractor.implement_position)}")

        result = tractor.raise_implement()
        print(f"\nAfter raise_implement(): {result}")
        print(f"Implement position: {tractor.implement_position}")
        print(f"Implement position (str): {str(tractor.implement_position)}")
        print(f"Implement position (repr): {repr(tractor.implement_position)}")

        # Check enum type
        from afs_fastapi.equipment.farm_tractors import ImplementPosition
        print(f"\nImplementPosition enum values:")
        for position in ImplementPosition:
            print(f"  {position.name}: {position.value}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_implement_position()