"""
FarmTractor Implementation Analysis Script

This script analyzes the FarmTractor class to verify it's a real implementation
with actual functionality, not a mock or stub.
"""

from afs_fastapi.equipment.farm_tractors import FarmTractor
import inspect
import sys
from pathlib import Path

def analyze_farm_tractor():
    """Analyze FarmTractor class implementation."""
    print("=== FarmTractor Class Analysis ===")

    try:
        cls = FarmTractor

        # Get public methods
        methods = [m for m in dir(cls) if not m.startswith('_')]
        print(f"Public methods: {methods}")

        # Get constructor signature
        try:
            init_sig = inspect.signature(cls.__init__)
            print(f"Init signature: {init_sig}")
        except Exception as e:
            print(f"Could not get init signature: {e}")

        # Check if it's a real implementation or mock
        try:
            source = inspect.getsource(cls)
            source_lines = len(source.splitlines())
            print(f"Source lines: {source_lines}")

            # Check for real implementation indicators
            has_conditions = 'if ' in source
            has_loops = 'for ' in source or 'while ' in source
            has_classes = 'class ' in source
            has_def = 'def ' in source

            print(f"Has conditional logic: {has_conditions}")
            print(f"Has loops: {has_loops}")
            print(f"Has class definitions: {has_classes}")
            print(f"Has function definitions: {has_def}")

            # Check for mock/stub indicators
            has_pass_only = source.strip().endswith('pass') and source_lines < 5
            has_not_implemented = 'NotImplementedError' in source or 'pass' in source

            print(f"Appears to be stub (pass only): {has_pass_only}")
            print(f"Has NotImplementedError: {has_not_implemented}")

        except OSError as e:
            print(f"Could not get source code: {e}")
            source_lines = 0
            has_conditions = has_loops = has_classes = has_def = False
            has_pass_only = has_not_implemented = True

        # Test actual instantiation with different parameters
        print("\n=== Testing Instantiation ===")

        # Try with make, model, year parameters (common pattern)
        try:
            tractor = FarmTractor("John Deere", "8RX", 2023)
            print(f"✅ Can instantiate (make, model, year): {tractor}")

            # Check attributes
            try:
                attrs = vars(tractor)
                print(f"✅ Has attributes: {list(attrs.keys())}")

                # Check for meaningful attribute values
                meaningful_attrs = any(
                    v is not None and v != "" and v != 0
                    for v in attrs.values()
                    if not isinstance(v, (type(None), bool))
                )
                print(f"✅ Has meaningful attribute values: {meaningful_attrs}")

            except Exception as e:
                print(f"❌ Cannot inspect attributes: {e}")

        except Exception as e:
            print(f"❌ Instantiation with (make, model, year) failed: {e}")

            # Try with no parameters
            try:
                tractor = FarmTractor()
                print(f"✅ Can instantiate (no params): {tractor}")
            except Exception as e2:
                print(f"❌ Instantiation with no params failed: {e2}")

                # Try with equipment_id parameter
                try:
                    tractor = FarmTractor(equipment_id="TRACTOR_001")
                    print(f"✅ Can instantiate (equipment_id): {tractor}")
                except Exception as e3:
                    print(f"❌ Instantiation with equipment_id failed: {e3}")

        # Test method functionality
        print("\n=== Testing Method Functionality ===")
        try:
            tractor = FarmTractor("John Deere", "8RX", 2023) if 'FarmTractor' in locals() else None
            if tractor:
                # Test a few key methods
                test_methods = ['get_status', 'start_engine', 'stop_engine', 'get_location']
                for method_name in test_methods:
                    if hasattr(tractor, method_name):
                        method = getattr(tractor, method_name)
                        if callable(method):
                            try:
                                result = method()
                                print(f"✅ Method {method_name}() returns: {type(result).__name__}")
                            except Exception as e:
                                print(f"❌ Method {method_name}() failed: {e}")
                        else:
                            print(f"⚠️  {method_name} is not callable")
                    else:
                        print(f"⚠️  Method {method_name} not found")
        except Exception as e:
            print(f"❌ Could not test methods: {e}")

        # Determine if it's a real implementation
        print("\n=== Assessment ===")
        is_real = (
            source_lines > 10 and
            (has_conditions or has_loops or has_def) and
            not has_pass_only
        )

        print(f"Real implementation: {'✅ YES' if is_real else '❌ NO'}")
        print(f"Confidence: {'HIGH' if source_lines > 50 else 'MEDIUM' if source_lines > 20 else 'LOW'}")

        return is_real

    except ImportError as e:
        print(f"❌ Could not import FarmTractor: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during analysis: {e}")
        return False

if __name__ == "__main__":
    result = analyze_farm_tractor()
    print(f"\n{'='*50}")
    print(f"FINAL RESULT: FarmTractor is {'REAL' if result else 'MOCK/STUB'}")
    print(f"{'='*50}")

    # Exit with appropriate code
    sys.exit(0 if result else 1)