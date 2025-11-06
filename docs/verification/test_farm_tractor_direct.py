"""
Direct FarmTractor Test Script

This script directly tests FarmTractor functionality without going through
the full FastAPI import chain to avoid dependency issues.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from afs_fastapi.equipment.farm_tractors import FarmTractor

def test_farm_tractor_functionality():
    """Test FarmTractor core functionality."""
    print("=== Direct FarmTractor Functionality Test ===")

    try:
        # Test 1: Basic instantiation
        print("1. Testing basic instantiation...")
        tractor = FarmTractor("John Deere", "8RX", 2023)
        print(f"✅ Created: {tractor}")

        # Test 2: Engine controls
        print("2. Testing engine controls...")
        result = tractor.start_engine()
        print(f"✅ Start engine result: {result}")
        assert tractor.engine_on == True

        result = tractor.stop_engine()
        print(f"✅ Stop engine result: {result}")
        assert tractor.engine_on == False

        # Test 3: Movement controls
        print("3. Testing movement controls...")
        tractor.start_engine()
        result = tractor.accelerate(10)
        print(f"✅ Accelerate result: {result}")
        assert tractor.speed == 10

        result = tractor.brake(5)
        print(f"✅ Brake result: {result}")
        assert tractor.speed == 5

        # Test 4: Gear controls
        print("4. Testing gear controls...")
        result = tractor.change_gear(3)
        print(f"✅ Change gear result: {result}")
        assert tractor.gear == 3

        # Test 5: GPS controls
        print("5. Testing GPS controls...")
        result = tractor.set_gps_position(40.7128, -74.0060)
        print(f"✅ Set GPS result: {result}")
        assert tractor.gps_latitude == 40.7128
        assert tractor.gps_longitude == -74.0060

        result = tractor.set_heading(90)
        print(f"✅ Set heading result: {result}")
        assert tractor.current_heading == 90

        # Test 6: Implement controls
        print("6. Testing implement controls...")
        result = tractor.lower_implement()
        print(f"✅ Lower implement result: {result}")
        assert tractor.implement_position == "lowered"

        result = tractor.raise_implement()
        print(f"✅ Raise implement result: {result}")
        assert tractor.implement_position == "raised"

        # Test 7: Power takeoff
        print("7. Testing power takeoff...")
        result = tractor.engage_power_takeoff()
        print(f"✅ Engage PTO result: {result}")
        assert tractor.power_takeoff == "engaged"

        result = tractor.disengage_power_takeoff()
        print(f"✅ Disengage PTO result: {result}")
        assert tractor.power_takeoff == "disengaged"

        # Test 8: Hydraulics
        print("8. Testing hydraulics...")
        result = tractor.activate_hydraulics()
        print(f"✅ Activate hydraulics result: {result}")
        assert tractor.hydraulics == "activated"

        result = tractor.deactivate_hydraulics()
        print(f"✅ Deactivate hydraulics result: {result}")
        assert tractor.hydraulics == "deactivated"

        # Test 9: Autonomous mode
        print("9. Testing autonomous mode...")
        result = tractor.enable_autonomous_mode()
        print(f"✅ Enable autonomous mode result: {result}")
        assert tractor.autonomous_mode == True

        result = tractor.disable_autonomous_mode()
        print(f"✅ Disable autonomous mode result: {result}")
        assert tractor.autonomous_mode == False

        # Test 10: Field operations
        print("10. Testing field operations...")
        result = tractor.start_field_work()
        print(f"✅ Start field work result: {result}")

        result = tractor.update_work_progress(1.5, 0.5)
        print(f"✅ Update work progress result: {result}")
        assert tractor.area_covered == 1.5
        assert tractor.work_rate == 0.5

        # Test 11: Safety systems
        print("11. Testing safety systems...")
        result = tractor.emergency_stop()
        print(f"✅ Emergency stop result: {result}")
        assert tractor.emergency_stop_active == True

        result = tractor.reset_emergency_stop()
        print(f"✅ Reset emergency stop result: {result}")
        assert tractor.emergency_stop_active == False

        # Test 12: Status and diagnostics
        print("12. Testing status and diagnostics...")
        status = tractor.get_status()
        print(f"✅ Get status result: {type(status).__name__}")
        assert status is not None

        diagnostics = tractor.get_engine_diagnostics()
        print(f"✅ Engine diagnostics: {type(diagnostics).__name__}")
        assert diagnostics is not None

        print("\n=== All Tests Passed! ===")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_farm_tractor_functionality()
    print(f"\n{'='*60}")
    print(f"DIRECT TEST RESULT: FarmTractor {'WORKS' if result else 'FAILED'}")
    print(f"{'='*60}")
    sys.exit(0 if result else 1)