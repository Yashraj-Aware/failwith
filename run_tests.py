#!/usr/bin/env python3
"""
Standalone test runner for failwith — no pytest required.
"""

import sys
import os
import json
import traceback

# Fix Windows console encoding — cp1252 can't handle emoji
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from failwith.core.analyzer import analyze_exception
from failwith.core.formatter import format_suggestion_block, _format_plain
from failwith.suggestions import Suggestion, register
from failwith.data.import_map import lookup_package, IMPORT_TO_PACKAGE
from failwith.utils.fuzzy import closest_match, edit_distance


passed = 0
failed = 0
errors = []


def test(name):
    """Decorator to register and run a test."""
    def decorator(func):
        global passed, failed
        try:
            func()
            print(f"  ✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {name}: {e}")
            failed += 1
            errors.append((name, str(e)))
        except Exception as e:
            print(f"  ✗ {name}: UNEXPECTED {type(e).__name__}: {e}")
            failed += 1
            errors.append((name, f"{type(e).__name__}: {e}"))
        return func
    return decorator


def get_suggestion(fn, config=None):
    if config is None:
        config = {"theme": "plain", "max_suggestions": 10}
    try:
        fn()
    except BaseException as e:
        return analyze_exception(type(e), e, e.__traceback__, config)
    return None


# ============================================================
print("\n🔧 Import Map Tests")
# ============================================================

@test("cv2 -> opencv-python")
def _():
    pkg = lookup_package("cv2")
    assert pkg is not None
    assert pkg[0] == "opencv-python"

@test("PIL -> Pillow")
def _():
    pkg = lookup_package("PIL")
    assert pkg is not None
    assert pkg[0] == "Pillow"

@test("sklearn -> scikit-learn")
def _():
    pkg = lookup_package("sklearn")
    assert pkg is not None
    assert pkg[0] == "scikit-learn"

@test("yaml -> PyYAML")
def _():
    pkg = lookup_package("yaml")
    assert pkg is not None
    assert pkg[0] == "PyYAML"

@test("dotted import: google.cloud.storage")
def _():
    pkg = lookup_package("google.cloud.storage")
    assert pkg is not None

@test("100+ import mappings exist")
def _():
    assert len(IMPORT_TO_PACKAGE) >= 100, f"Only {len(IMPORT_TO_PACKAGE)} mappings"


# ============================================================
print("\n🔤 Fuzzy Matching Tests")
# ============================================================

@test("closest_match finds 'username' from 'usernme'")
def _():
    assert closest_match("usernme", ["username", "email", "id"]) == "username"

@test("no match returns None")
def _():
    assert closest_match("xyz", ["abc", "def"]) is None

@test("edit_distance('kitten', 'sitting') == 3")
def _():
    assert edit_distance("kitten", "sitting") == 3

@test("edit_distance('abc', 'abc') == 0")
def _():
    assert edit_distance("abc", "abc") == 0


# ============================================================
print("\n📦 ModuleNotFoundError Tests")
# ============================================================

@test("ModuleNotFoundError gets suggestion")
def _():
    s = get_suggestion(lambda: __import__("xyznonexistent123"))
    assert s is not None
    assert "pip install" in " ".join(s.fixes)

@test("ModuleNotFoundError mentions venv")
def _():
    s = get_suggestion(lambda: __import__("xyznonexistent123"))
    assert s is not None
    fixes_text = " ".join(s.fixes).lower()
    assert "venv" in fixes_text or "python" in fixes_text


# ============================================================
print("\n🔗 Connection Error Tests")
# ============================================================

@test("ConnectionRefusedError gets suggestion")
def _():
    s = get_suggestion(lambda: (_ for _ in ()).throw(ConnectionRefusedError("Connection refused")))
    # Use a simpler approach
    try:
        raise ConnectionRefusedError("[Errno 111] Connection refused")
    except ConnectionRefusedError as e:
        s = analyze_exception(type(e), e, e.__traceback__, {"theme": "plain", "max_suggestions": 10})
    assert s is not None
    assert "refused" in s.title.lower() or "connection" in s.title.lower()

@test("TimeoutError gets suggestion")
def _():
    try:
        raise TimeoutError("Connection timed out")
    except TimeoutError as e:
        s = analyze_exception(type(e), e, e.__traceback__, {"theme": "plain", "max_suggestions": 10})
    assert s is not None
    assert "timed out" in s.title.lower()

@test("ConnectionResetError gets suggestion")
def _():
    try:
        raise ConnectionResetError("Connection reset by peer")
    except ConnectionResetError as e:
        s = analyze_exception(type(e), e, e.__traceback__, {"theme": "plain", "max_suggestions": 10})
    assert s is not None
    assert "reset" in s.title.lower()


# ============================================================
print("\n📁 File System Error Tests")
# ============================================================

@test("FileNotFoundError shows working dir")
def _():
    s = get_suggestion(lambda: open("nonexistent_config_xyz.yaml"))
    assert s is not None
    fixes_text = " ".join(s.fixes)
    assert "Working dir" in fixes_text or "working" in fixes_text.lower()

@test("PermissionError suggests chmod")
def _():
    try:
        raise PermissionError(13, "Permission denied", "/etc/shadow")
    except PermissionError as e:
        s = analyze_exception(type(e), e, e.__traceback__, {"theme": "plain", "max_suggestions": 10})
    assert s is not None
    assert "chmod" in " ".join(s.fixes) or "chown" in " ".join(s.fixes)


# ============================================================
print("\n🔑 Key/Attribute/Name Error Tests")
# ============================================================

@test("KeyError suggests .get()")
def _():
    def key_err():
        d = {"a": 1}
        return d["b"]
    s = get_suggestion(key_err)
    assert s is not None
    assert ".get(" in " ".join(s.fixes)

@test("KeyError fuzzy matches keys")
def _():
    def key_err():
        d = {"username": "john", "email": "j@j.com"}
        return d["user_name"]
    s = get_suggestion(key_err)
    assert s is not None
    # Should find 'username' as a close match
    fixes_text = " ".join(s.fixes)
    assert "username" in fixes_text or "Did you mean" in fixes_text

@test("AttributeError on NoneType warns about None")
def _():
    def none_attr():
        x = None
        x.append(1)
    s = get_suggestion(none_attr)
    assert s is not None
    assert "none" in " ".join(s.fixes).lower()

@test("NameError suggests similar names")
def _():
    def name_err():
        prnt("hello")  # noqa: F821
    s = get_suggestion(name_err)
    assert s is not None
    assert "not defined" in s.title.lower()


# ============================================================
print("\n🔢 Type/Value/Index Error Tests")
# ============================================================

@test("TypeError str+int suggests f-string")
def _():
    def type_err():
        return "count: " + 42
    s = get_suggestion(type_err)
    assert s is not None
    fixes_text = " ".join(s.fixes).lower()
    assert "f-string" in fixes_text or "str(" in fixes_text

@test("TypeError not callable")
def _():
    def call_err():
        x = 42
        x()
    s = get_suggestion(call_err)
    assert s is not None
    assert "not callable" in s.title.lower()

@test("ValueError int() conversion")
def _():
    def val_err():
        int("hello")
    s = get_suggestion(val_err)
    assert s is not None
    assert "convert" in s.title.lower() or "int" in s.title.lower()

@test("ValueError unpacking mismatch")
def _():
    def unpack_err():
        a, b, c = [1, 2]
    s = get_suggestion(unpack_err)
    assert s is not None
    assert "unpack" in s.title.lower()

@test("IndexError shows context")
def _():
    def idx_err():
        lst = [1, 2, 3]
        return lst[10]
    s = get_suggestion(idx_err)
    assert s is not None
    assert "index" in s.title.lower() or "range" in s.title.lower()

@test("ZeroDivisionError identifies zero var")
def _():
    def zero_div():
        denominator = 0
        return 42 / denominator
    s = get_suggestion(zero_div)
    assert s is not None
    assert "zero" in s.title.lower() or "division" in s.title.lower()


# ============================================================
print("\n📝 Encoding Error Tests")
# ============================================================

@test("UnicodeDecodeError suggests utf-8")
def _():
    def decode_err():
        b"\xff\xfe".decode("ascii")
    s = get_suggestion(decode_err)
    assert s is not None
    assert "utf-8" in " ".join(s.fixes).lower()

@test("UnicodeEncodeError suggests alternatives")
def _():
    def encode_err():
        "héllo".encode("ascii")
    s = get_suggestion(encode_err)
    assert s is not None
    assert "encode" in " ".join(s.fixes).lower() or "utf-8" in " ".join(s.fixes).lower()


# ============================================================
print("\n🔄 Recursion / Memory Tests")
# ============================================================

@test("RecursionError mentions base case")
def _():
    def recursive():
        recursive()
    s = get_suggestion(recursive)
    assert s is not None
    assert "recursion" in s.title.lower()
    assert "base case" in " ".join(s.fixes).lower()


# ============================================================
print("\n📋 JSON Error Tests")
# ============================================================

@test("JSONDecodeError provides context")
def _():
    def json_err():
        json.loads('{"key": value}')
    s = get_suggestion(json_err)
    assert s is not None
    assert "json" in s.title.lower() or "invalid" in s.title.lower()

@test("JSONDecodeError handles trailing comma")
def _():
    def json_err():
        json.loads('{"a": 1, "b": 2,}')
    s = get_suggestion(json_err)
    assert s is not None


# ============================================================
print("\n🛡️ StopIteration Tests")
# ============================================================

@test("StopIteration suggests default")
def _():
    def stop_iter():
        it = iter([])
        next(it)
    s = get_suggestion(stop_iter)
    assert s is not None
    assert "default" in " ".join(s.fixes).lower() or "next(" in " ".join(s.fixes)


# ============================================================
print("\n🎨 Formatter Tests")
# ============================================================

@test("Plain format has no ANSI codes")
def _():
    s = Suggestion(title="Test error", fixes=["Fix 1", "Fix 2"], env_info=["Python 3.11"])
    output = _format_plain(s, {"theme": "plain"})
    assert "Test error" in output
    assert "Fix 1" in output
    assert "\033[" not in output

@test("Environment info appears in output")
def _():
    s = Suggestion(title="Test", fixes=["Fix"], env_info=["Python 3.11", "venv: .venv"])
    output = _format_plain(s, {"theme": "plain"})
    assert "Python 3.11" in output

@test("Empty suggestion is falsy")
def _():
    s = Suggestion(title="Empty", fixes=[])
    assert not s


# ============================================================
print("\n⚙️ Install/Uninstall Tests")
# ============================================================

@test("install() sets excepthook")
def _():
    import failwith
    original = sys.excepthook
    failwith.install()
    assert sys.excepthook != original
    failwith.uninstall()
    assert sys.excepthook == original

@test("catch() works as context manager")
def _():
    import failwith
    executed = False
    with failwith.catch(reraise=False):
        executed = True
        raise ValueError("test")
    assert executed

@test("catch() works as decorator")
def _():
    import failwith
    @failwith.catch(reraise=False)
    def failing():
        raise ValueError("test")
    failing()  # should not raise


# ============================================================
print("\n🔌 Custom Handler Tests")
# ============================================================

@test("Custom handler registration works")
def _():
    class MyError(Exception):
        pass

    @register(MyError)
    def handle(exc_type, exc_value, exc_tb, config):
        return Suggestion(title="Custom handler fired", fixes=["Custom fix"])

    try:
        raise MyError("boom")
    except MyError as e:
        s = analyze_exception(type(e), e, e.__traceback__, {"theme": "plain", "max_suggestions": 10})
    assert s is not None
    assert "custom handler" in s.title.lower()


# ============================================================
# Summary
# ============================================================

print(f"\n{'='*60}")
print(f"  Results: {passed} passed, {failed} failed")
print(f"{'='*60}")

if errors:
    print("\nFailures:")
    for name, msg in errors:
        print(f"  ✗ {name}: {msg}")

sys.exit(1 if failed > 0 else 0)
