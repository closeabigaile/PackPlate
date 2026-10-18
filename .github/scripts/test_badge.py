"""Turn pytest JUnit XML files into the test-count badge's message and color.

Usage: python test_badge.py RESULTS.xml [RESULTS.xml ...]
Prints `message=...` and `color=...` lines for $GITHUB_OUTPUT.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

passed = failed = 0
missing = []
for path in map(Path, sys.argv[1:]):
    if not path.exists():
        missing.append(path.name)
        continue
    for suite in ET.parse(path).getroot().iter("testsuite"):
        total = int(suite.get("tests", 0))
        bad = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
        failed += bad
        passed += total - bad - int(suite.get("skipped", 0))

if missing:
    # A suite didn't produce results (e.g. it crashed before running).
    print(f"message=no results ({', '.join(missing)})")
    print("color=red")
elif failed:
    print(f"message={failed} failed, {passed} passed")
    print("color=red")
else:
    print(f"message={passed} passed")
    print("color=brightgreen")
