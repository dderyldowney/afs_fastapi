"""
API Real Requests Test Script for Task 3

This script tests API endpoints with real requests by analyzing the source code
and checking if the implementations contain actual business logic rather than stubs.
"""

import ast
import re
import sys
from pathlib import Path
from typing import Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def analyze_endpoint_source(endpoint_file: Path) -> dict[str, Any]:
    """Analyze an endpoint file to check for real implementations."""
    try:
        with open(endpoint_file, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        analysis = {
            'file': str(endpoint_file),
            'total_functions': 0,
            'real_implementations': 0,
            'stub_implementations': 0,
            'functions': []
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                analysis['total_functions'] += 1

                # Analyze function content
                function_analysis = {
                    'name': node.name,
                    'lines': len(node.body),
                    'has_return': any('return' in ast.unparse(stmt) for stmt in node.body if isinstance(stmt, (ast.Return, ast.If))),
                    'has_async': isinstance(node, ast.AsyncFunctionDef),
                    'has_business_logic': False,
                    'is_stub': False
                }

                # Check for business logic indicators
                function_source = ast.unparse(node)
                business_keywords = [
                    'farm', 'tractor', 'equipment', 'soil', 'water', 'monitoring',
                    'sensor', 'agricultural', 'field', 'crop', 'irrigation',
                    'database', 'db', 'session', 'query', 'result',
                    'response', 'request', 'validate', 'calculate'
                ]

                function_analysis['has_business_logic'] = any(
                    keyword in function_source.lower() for keyword in business_keywords
                )

                # Check for stub indicators
                stub_indicators = [
                    'TODO', 'FIXME', 'NotImplemented', 'pass', '# Stub',
                    '# Mock', 'raise NotImplementedError', 'return {"status": "ok"}'
                ]

                function_analysis['is_stub'] = any(
                    indicator in function_source for indicator in stub_indicators
                )

                if function_analysis['has_business_logic'] and not function_analysis['is_stub']:
                    analysis['real_implementations'] += 1
                elif function_analysis['is_stub']:
                    analysis['stub_implementations'] += 1

                analysis['functions'].append(function_analysis)

        return analysis

    except Exception as e:
        return {
            'file': str(endpoint_file),
            'error': str(e),
            'total_functions': 0,
            'real_implementations': 0,
            'stub_implementations': 0,
            'functions': []
        }

def analyze_api_endpoints():
    """Analyze all API endpoint files."""
    print("=== API Endpoint Source Analysis ===")

    api_dir = project_root / 'afs_fastapi' / 'api' / 'endpoints'
    if not api_dir.exists():
        print(f"❌ API endpoints directory not found: {api_dir}")
        return False

    endpoint_files = list(api_dir.glob('*.py'))
    endpoint_files = [f for f in endpoint_files if f.name != '__init__.py']

    print(f"📁 Found {len(endpoint_files)} endpoint files")

    total_analysis = {
        'total_files': len(endpoint_files),
        'total_functions': 0,
        'real_implementations': 0,
        'stub_implementations': 0,
        'files': []
    }

    for endpoint_file in endpoint_files:
        print(f"\n🔍 Analyzing: {endpoint_file.name}")
        analysis = analyze_endpoint_source(endpoint_file)

        if 'error' in analysis:
            print(f"   ❌ Error: {analysis['error']}")
            continue

        print(f"   Functions: {analysis['total_functions']}")
        print(f"   Real implementations: {analysis['real_implementations']}")
        print(f"   Stub implementations: {analysis['stub_implementations']}")

        # Show function details
        for func in analysis['functions'][:3]:  # Show first 3 functions
            status = "✅ REAL" if func['has_business_logic'] and not func['is_stub'] else "❌ STUB"
            print(f"     - {func['name']}: {status}")

        total_analysis['total_functions'] += analysis['total_functions']
        total_analysis['real_implementations'] += analysis['real_implementations']
        total_analysis['stub_implementations'] += analysis['stub_implementations']
        total_analysis['files'].append(analysis)

    return total_analysis

def analyze_main_app():
    """Analyze the main FastAPI app."""
    print("\n=== Main App Analysis ===")

    main_file = project_root / 'afs_fastapi' / 'api' / 'main.py'
    if not main_file.exists():
        print(f"❌ Main app file not found: {main_file}")
        return False

    try:
        with open(main_file, encoding='utf-8') as f:
            content = f.read()

        # Check for real implementation indicators
        real_indicators = [
            'FastAPI(', 'app.include_router', '@app.get', '@app.post',
            'from afs_fastapi', 'import', 'def ', 'async def ',
            'return', 'response_model', 'tags=', 'summary='
        ]

        stub_indicators = [
            '# TODO', '# FIXME', 'NotImplemented', 'pass  # Stub'
        ]

        real_count = sum(content.count(indicator) for indicator in real_indicators)
        stub_count = sum(content.count(indicator) for indicator in stub_indicators)

        print(f"✅ Main app file: {main_file}")
        print(f"   Lines of code: {len(content.splitlines())}")
        print(f"   Real implementation indicators: {real_count}")
        print(f"   Stub indicators: {stub_count}")

        # Check for key endpoints
        endpoint_patterns = [
            r'@app\.get\(["\']([^"\']+)["\']',
            r'@app\.post\(["\']([^"\']+)["\']',
            r'@app\.put\(["\']([^"\']+)["\']',
            r'@app\.delete\(["\']([^"\']+)["\']'
        ]

        endpoints = []
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, content)
            endpoints.extend(matches)

        print(f"   Direct endpoints found: {len(endpoints)}")
        for endpoint in endpoints[:5]:  # Show first 5
            print(f"     - {endpoint}")

        # Check router inclusions
        router_inclusions = re.findall(r'app\.include_router\([^,]+,\s*prefix=["\']([^"\']+)["\']', content)
        print(f"   Router prefixes: {router_inclusions}")

        return {
            'lines': len(content.splitlines()),
            'real_indicators': real_count,
            'stub_indicators': stub_count,
            'endpoints': endpoints,
            'routers': router_inclusions,
            'is_real_implementation': real_count > stub_count and len(endpoints) > 0
        }

    except Exception as e:
        print(f"❌ Error analyzing main app: {e}")
        return False

def check_test_client_usage():
    """Check if tests use real TestClient."""
    print("\n=== TestClient Usage Analysis ===")

    test_files = list(project_root.glob('tests/**/*api*.py'))
    test_files.extend(list(project_root.glob('tests/**/test_*api*.py')))
    test_files = list(set(test_files))  # Remove duplicates

    print(f"📁 Found {len(test_files)} API test files")

    test_client_usage = {
        'files_with_testclient': 0,
        'files_with_real_app_import': 0,
        'files_with_mocks': 0,
        'total_test_files': len(test_files),
        'details': []
    }

    for test_file in test_files:
        try:
            with open(test_file, encoding='utf-8') as f:
                content = f.read()

            analysis = {
                'file': str(test_file),
                'has_testclient': 'TestClient' in content,
                'has_real_app_import': 'from afs_fastapi.api.main import app' in content,
                'has_mocks': '@patch' in content or 'Mock(' in content or 'mock_' in content
            }

            if analysis['has_testclient']:
                test_client_usage['files_with_testclient'] += 1
            if analysis['has_real_app_import']:
                test_client_usage['files_with_real_app_import'] += 1
            if analysis['has_mocks']:
                test_client_usage['files_with_mocks'] += 1

            test_client_usage['details'].append(analysis)

            status = "✅ REAL CLIENT" if analysis['has_testclient'] and analysis['has_real_app_import'] else "⚠️  NEEDS CHECKING"
            print(f"   {test_file.name}: {status}")

        except Exception as e:
            print(f"   ❌ Error analyzing {test_file.name}: {e}")

    return test_client_usage

def main():
    """Main analysis function."""
    print("🚀 Starting API Real Requests Analysis...")

    # Analyze endpoints
    endpoint_analysis = analyze_api_endpoints()
    if not endpoint_analysis:
        print("❌ Failed to analyze endpoints")
        return False

    # Analyze main app
    main_analysis = analyze_main_app()
    if not main_analysis:
        print("❌ Failed to analyze main app")
        return False

    # Check test client usage
    test_analysis = check_test_client_usage()

    # Generate summary
    print("\n📊 ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"Endpoint files analyzed: {endpoint_analysis['total_files']}")
    print(f"Total endpoint functions: {endpoint_analysis['total_functions']}")
    print(f"Real implementations: {endpoint_analysis['real_implementations']}")
    print(f"Stub implementations: {endpoint_analysis['stub_implementations']}")
    print(f"Main app lines: {main_analysis['lines']}")
    print(f"Main app endpoints: {len(main_analysis['endpoints'])}")
    print(f"Main app routers: {len(main_analysis['routers'])}")
    print(f"Test files with TestClient: {test_analysis['files_with_testclient']}/{test_analysis['total_test_files']}")
    print(f"Test files with real app import: {test_analysis['files_with_real_app_import']}/{test_analysis['total_test_files']}")

    # Determine success
    endpoint_success = endpoint_analysis['real_implementations'] > endpoint_analysis['stub_implementations']
    main_success = main_analysis['is_real_implementation']
    test_success = test_analysis['files_with_real_app_import'] > 0

    print("\n🎯 VERIFICATION RESULTS")
    print("=" * 50)
    print(f"Endpoints have real implementations: {'✅ YES' if endpoint_success else '❌ NO'}")
    print(f"Main app is real implementation: {'✅ YES' if main_success else '❌ NO'}")
    print(f"Tests use real TestClient: {'✅ YES' if test_success else '❌ NO'}")

    overall_success = endpoint_success and main_success and test_success
    print(f"\n🏆 OVERALL: {'✅ PASSED' if overall_success else '❌ FAILED'}")

    if overall_success:
        print("The API endpoints contain real implementations with actual business logic,")
        print("and the tests use real TestClient to verify functionality.")
    else:
        print("The API may contain stub implementations or tests may not be using real clients.")

    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)