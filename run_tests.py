"""Run the suite without requiring pytest.

pytest is the nicer runner and the suite is written to work under it, but the
tests are plain asserts on purpose so that a checkout with only the runtime
dependencies installed can still verify itself.
"""
import sys, traceback
sys.path.insert(0, ".")
import tests.test_pipeline as T

passed = failed = 0
for name in sorted(n for n in dir(T) if n.startswith("test_")):
    try:
        getattr(T, name)()
        passed += 1
        print(f"  ok  {name}")
    except Exception:
        failed += 1
        print(f"FAIL  {name}")
        traceback.print_exc()
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
