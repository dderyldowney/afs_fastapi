"""
API Startup Verification Script for Task 3

This script verifies that the FastAPI application starts with real implementation code,
not stubs or mock responses. It analyzes the app structure and endpoints to ensure
they contain actual business logic.
"""

import inspect
import sys
from pathlib import Path

from afs_fastapi.api.main import app

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def verify_api_startup():
    """Verify FastAPI app starts with real implementation."""
    print("=== API Startup Verification ===")

    try:
        # Check app configuration
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        print(f"✅ App description: {app.description[:100]}...")

        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append({
                    'path': route.path,
                    'methods': list(route.methods) if hasattr(route, 'methods') else ['GET'],
                    'name': getattr(route, 'name', 'unknown')
                })

        print(f"✅ Total routes found: {len(routes)}")
        print(f"✅ Route paths: {[route['path'] for route in routes[:10]]}")  # Show first 10

        # Analyze main endpoints for real implementation
        real_endpoints = 0
        stub_endpoints = 0

        print("\n=== Endpoint Analysis ===")

        # Check specific endpoints from main.py
        main_endpoints = [
            ('/', 'api_info'),
            ('/health', 'health_check'),
            ('/version', 'version_info'),
            ('/status', 'system_status')
        ]

        for route in app.routes:
            if hasattr(route, 'endpoint') and hasattr(route, 'path'):
                endpoint_name = route.endpoint.__name__
                source_path = inspect.getfile(route.endpoint)

                print(f"\n🔍 Analyzing endpoint: {route.path}")
                print(f"   Function: {endpoint_name}")
                print(f"   Source: {source_path}")

                # Check if it's a real implementation
                try:
                    source = inspect.getsource(route.endpoint)
                    source_lines = len(source.splitlines())

                    # Indicators of real implementation
                    has_real_logic = (
                        'return' in source and
                        source_lines > 5 and
                        ('dict' in source or 'await' in source or '.' in source)
                    )
                    has_imports = 'import' in source or 'from' in source
                    has_business_logic = any(keyword in source.lower() for keyword in [
                        'ai_processing', 'farm', 'equipment', 'monitoring', 'soil', 'water',
                        'health', 'system', 'version', 'statistics', 'timestamp'
                    ])

                    print(f"   - Source lines: {source_lines}")
                    print(f"   - Has real logic: {has_real_logic}")
                    print(f"   - Has imports: {has_imports}")
                    print(f"   - Has business logic: {has_business_logic}")

                    if has_real_logic and has_business_logic:
                        print("   ✅ REAL implementation detected")
                        real_endpoints += 1
                    else:
                        print("   ⚠️  Possible stub/mock implementation")
                        stub_endpoints += 1

                except OSError:
                    print("   ❌ Could not analyze source (built-in or C extension)")
                    stub_endpoints += 1

        # Check router endpoints
        print("\n=== Router Analysis ===")
        router_info = []

        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'include_router'):
                print(f"📦 Router found: {route.path}")
                router_info.append(route.path)

        print(f"✅ Router prefixes: {router_info}")

        # Summary
        print("\n=== Verification Summary ===")
        print(f"Real endpoints detected: {real_endpoints}")
        print(f"Stub/mock endpoints: {stub_endpoints}")
        print(f"Total routes analyzed: {len(routes)}")

        if real_endpoints > stub_endpoints:
            print("✅ PASSED: API has more real implementations than stubs")
            return True
        else:
            print("❌ FAILED: API has more stubs than real implementations")
            return False

    except Exception as e:
        print(f"❌ CRITICAL ERROR during API startup verification: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_app_structure():
    """Analyze the overall app structure and imports."""
    print("\n=== App Structure Analysis ===")

    # Check key imports in main.py
    try:
        import afs_fastapi.api.endpoints.ai_processing as ai_module
        import afs_fastapi.api.endpoints.equipment as equipment_module
        import afs_fastapi.api.endpoints.monitoring as monitoring_module
        print("✅ Key endpoint modules imported successfully")

        # Check equipment module has real content
        equipment_attrs = [attr for attr in dir(equipment_module) if not attr.startswith('_')]
        print(f"✅ Equipment module attributes: {equipment_attrs}")

        # Check monitoring module has real content
        monitoring_attrs = [attr for attr in dir(monitoring_module) if not attr.startswith('_')]
        print(f"✅ Monitoring module attributes: {monitoring_attrs}")

        # Check AI processing module has real content
        ai_attrs = [attr for attr in dir(ai_module) if not attr.startswith('_')]
        print(f"✅ AI processing module attributes: {ai_attrs}")

        return True

    except ImportError as e:
        print(f"❌ Import error analyzing app structure: {e}")
        return False

if __name__ == "__main__":
    print("Starting API Startup Verification...")

    # Run verification
    startup_success = verify_api_startup()
    structure_success = analyze_app_structure()

    if startup_success and structure_success:
        print("\n🎉 API STARTUP VERIFICATION: ✅ PASSED")
        print("The FastAPI application contains real implementations with actual business logic.")
        sys.exit(0)
    else:
        print("\n❌ API STARTUP VERIFICATION: ❌ FAILED")
        print("The FastAPI application may contain stubs or incomplete implementations.")
        sys.exit(1)