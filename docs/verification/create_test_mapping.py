# docs/verification/create_test_mapping.py
import json
import re
from pathlib import Path


def map_tests_to_source():
    """Map test files to their corresponding source files."""
    test_mapping = {}

    for test_file in Path("tests").rglob("*.py"):
        with open(test_file) as f:
            content = f.read()

        # Find imports from afs_fastapi
        imports = re.findall(r"from afs_fastapi\.([^\s]+) import|import afs_fastapi\.([^\s]+)", content)

        test_mapping[str(test_file)] = {
            "imports": [match[0] or match[1] for match in imports],
            "test_count": len(re.findall(r"def test_", content)),
            "has_async": "async def test_" in content,
            "has_integration": "integration" in str(test_file).lower()
        }

    return test_mapping

if __name__ == "__main__":
    mapping = map_tests_to_source()
    with open("docs/verification/test_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)