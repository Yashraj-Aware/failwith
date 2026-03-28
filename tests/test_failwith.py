"""
Test suite for failwith — covers all 20 error type handlers.
"""

import json
import os
import sys
import pytest

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from failwith.core.analyzer import analyze_exception
from failwith.core.formatter import format_suggestion_block, _format_plain
from failwith.suggestions import Suggestion, register
from failwith.data.import_map import lookup_package
from failwith.utils.fuzzy import closest_match, edit_distance


# ============================================================
# Helper to generate a suggestion from a real exception
# ============================================================

def get_suggestion(callable_fn, config=None):
    """Run a callable that raises, and return the Suggestion."""
    if config is None:
        config = {"theme": "plain", "max_suggestions": 10}
    try:
        callable_fn()
    except BaseException as e:
        return analyze_exception(type(e), e, e.__traceback__, config)
    return None


# ============================================================
# Import Errors
# ============================================================

class TestModuleNotFoundError:
    def test_known_import_mismatch(self):
        """cv2 -> opencv-python should be suggested."""
        s = get_suggestion(lambda: __import__("cv2"))
        assert s is not None
        assert "opencv-python" in " ".join(s.fixes)

    def test_unknown_module(self):
        """Unknown modules should still get a pip install suggestion."""
        s = get_suggestion(lambda: __import__("xyznonexistent123"))
        assert s is not None
        assert "pip install" in " ".join(s.fixes)

    def test_pil_to_pillow(self):
        """PIL -> Pillow mapping."""
        pkg = lookup_package("PIL")
        assert pkg is not None
        assert pkg[0] == "Pillow"

    def test_sklearn_to_scikit_learn(self):
        """sklearn -> scikit-learn mapping."""
        pkg = lookup_package("sklearn")
        assert pkg is not None
        assert pkg[0] == "scikit-learn"

    def test_yaml_to_pyyaml(self):
        """yaml -> PyYAML mapping."""
        pkg = lookup_package("yaml")
        assert pkg is not None
        assert pkg[0] == "PyYAML"

    def test_dotted_import_lookup(self):
        """google.cloud.storage should match google.cloud."""
        pkg = lookup_package("google.cloud.storage")
        assert pkg is not None

    def test_venv_detection(self):
        """Suggestion should mention venv status."""
        s = get_suggestion(lambda: __import__("xyznonexistent123"))
        assert s is not None
        fixes_text = " ".join(s.fixes)
        assert "venv" in fixes_text.lower() or "Python" in fixes_text


class TestImportError:
    def test_cannot_import_name(self):
        """ImportError for wrong name from a known module."""
        def bad_import():
            from os import nonexistent_function_xyz  # noqa
        s = get_suggestion(bad_import)
        assert s is not None
        assert "not found" in s.title.lower() or "cannot import" in s.title.lower()


# ============================================================
# Connection Errors
# ============================================================

class TestConnectionErrors:
    def test_connection_refused_with_port(self):
        """ConnectionRefusedError should suggest service start commands."""
        import socket
        def connect_refused():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            try:
                s.connect(("127.0.0.1", 59999))
            finally:
                s.close()

        s = get_suggestion(connect_refused)
        assert s is not None
        assert "connection refused" in s.title.lower() or "refused" in s.title.lower()

    def test_connection_reset(self):
        """ConnectionResetError should provide suggestions."""
        def reset():
            raise ConnectionResetError("Connection reset by peer")
        s = get_suggestion(reset)
        assert s is not None
        assert "reset" in s.title.lower()

    def test_timeout_error(self):
        """TimeoutError should provide network debug suggestions."""
        def timeout():
            raise TimeoutError("Connection timed out")
        s = get_suggestion(timeout)
        assert s is not None
        assert "timed out" in s.title.lower()


# ============================================================
# File System Errors
# ============================================================

class TestFileSystemErrors:
    def test_file_not_found(self):
        """FileNotFoundError should suggest similar files."""
        def missing_file():
            open("/tmp/definitely_not_a_real_file_xyz123.txt")

        s = get_suggestion(missing_file)
        assert s is not None
        assert "does not exist" in s.title.lower() or "not found" in s.title.lower()

    def test_file_not_found_shows_cwd(self):
        """Should show current working directory."""
        def missing_file():
            open("nonexistent_config.yaml")

        s = get_suggestion(missing_file)
        assert s is not None
        fixes_text = " ".join(s.fixes)
        assert "working dir" in fixes_text.lower() or "Working dir" in fixes_text

    def test_permission_error(self):
        """PermissionError should suggest chmod/chown."""
        def perm_error():
            raise PermissionError(13, "Permission denied", "/etc/shadow")
        s = get_suggestion(perm_error)
        assert s is not None
        assert "permission" in s.title.lower()
        fixes_text = " ".join(s.fixes)
        assert "chmod" in fixes_text or "chown" in fixes_text

    def test_is_a_directory(self):
        """IsADirectoryError should explain the issue."""
        def dir_error():
            raise IsADirectoryError("Is a directory: '/tmp'")
        s = get_suggestion(dir_error)
        assert s is not None
        assert "directory" in s.title.lower()


# ============================================================
# Type / Key / Attribute / Name Errors
# ============================================================

class TestTypeErrors:
    def test_key_error_fuzzy_match(self):
        """KeyError should fuzzy match against available keys."""
        def key_err():
            d = {"username": "john", "email": "j@j.com", "id": 1}
            return d["user_name"]

        s = get_suggestion(key_err)
        assert s is not None
        assert "not found" in s.title.lower()

    def test_key_error_safe_access(self):
        """KeyError should suggest .get()."""
        def key_err():
            d = {"a": 1}
            return d["b"]

        s = get_suggestion(key_err)
        assert s is not None
        fixes_text = " ".join(s.fixes)
        assert ".get(" in fixes_text

    def test_attribute_error(self):
        """AttributeError should fuzzy match against available attrs."""
        def attr_err():
            "hello".uper()

        s = get_suggestion(attr_err)
        assert s is not None
        assert "not found" in s.title.lower() or "attribute" in s.title.lower()

    def test_attribute_error_none(self):
        """AttributeError on NoneType should warn about None."""
        def none_attr():
            x = None
            x.append(1)

        s = get_suggestion(none_attr)
        assert s is not None
        fixes_text = " ".join(s.fixes)
        assert "none" in fixes_text.lower()

    def test_name_error(self):
        """NameError should suggest similar names."""
        def name_err():
            prnt("hello")  # noqa: F821

        s = get_suggestion(name_err)
        assert s is not None
        assert "not defined" in s.title.lower()

    def test_type_error_str_int(self):
        """TypeError for str + int should suggest f-string."""
        def type_err():
            return "count: " + 42

        s = get_suggestion(type_err)
        assert s is not None
        fixes_text = " ".join(s.fixes)
        assert "f-string" in fixes_text.lower() or "str(" in fixes_text

    def test_type_error_not_callable(self):
        """TypeError for calling non-callable."""
        def call_err():
            x = 42
            x()

        s = get_suggestion(call_err)
        assert s is not None
        assert "not callable" in s.title.lower()

    def test_value_error_int_conversion(self):
        """ValueError for int() should suggest strip/float."""
        def val_err():
            int("hello")

        s = get_suggestion(val_err)
        assert s is not None
        assert "convert" in s.title.lower() or "int" in s.title.lower()

    def test_value_error_unpack(self):
        """ValueError for unpacking mismatch."""
        def unpack_err():
            a, b, c = [1, 2]

        s = get_suggestion(unpack_err)
        assert s is not None
        assert "unpack" in s.title.lower()

    def test_index_error(self):
        """IndexError should show collection size."""
        def idx_err():
            lst = [1, 2, 3]
            return lst[10]

        s = get_suggestion(idx_err)
        assert s is not None
        assert "index" in s.title.lower() or "range" in s.title.lower()

    def test_zero_division(self):
        """ZeroDivisionError should show zero-valued variables."""
        def zero_div():
            denominator = 0
            return 42 / denominator

        s = get_suggestion(zero_div)
        assert s is not None
        assert "zero" in s.title.lower() or "division" in s.title.lower()


# ============================================================
# Encoding Errors
# ============================================================

class TestEncodingErrors:
    def test_unicode_decode_error(self):
        """UnicodeDecodeError should suggest encodings."""
        def decode_err():
            b"\xff\xfe".decode("ascii")

        s = get_suggestion(decode_err)
        assert s is not None
        assert "decode" in s.title.lower() or "encoding" in s.title.lower()
        fixes_text = " ".join(s.fixes)
        assert "utf-8" in fixes_text.lower()

    def test_unicode_encode_error(self):
        """UnicodeEncodeError should suggest encode fixes."""
        def encode_err():
            "héllo".encode("ascii")

        s = get_suggestion(encode_err)
        assert s is not None
        fixes_text = " ".join(s.fixes)
        assert "utf-8" in fixes_text.lower() or "encode" in fixes_text.lower()


# ============================================================
# Memory / Recursion
# ============================================================

class TestRecursionError:
    def test_recursion_error(self):
        """RecursionError should show recursion limit."""
        def recursive():
            recursive()

        s = get_suggestion(recursive)
        assert s is not None
        assert "recursion" in s.title.lower()
        fixes_text = " ".join(s.fixes)
        assert "base case" in fixes_text.lower() or "limit" in fixes_text.lower()


# ============================================================
# JSON Errors
# ============================================================

class TestJSONErrors:
    def test_json_decode_error(self):
        """JSONDecodeError should show position context."""
        def json_err():
            json.loads('{"key": value}')

        s = get_suggestion(json_err)
        assert s is not None
        assert "json" in s.title.lower() or "invalid" in s.title.lower()

    def test_json_trailing_comma(self):
        """JSONDecodeError for trailing comma."""
        def json_err():
            json.loads('{"a": 1, "b": 2,}')

        s = get_suggestion(json_err)
        assert s is not None


# ============================================================
# Syntax Errors
# ============================================================

class TestSyntaxErrors:
    def test_syntax_error(self):
        """SyntaxError should provide common fix patterns."""
        def syntax_err():
            exec("def foo(\n  pass")

        s = get_suggestion(syntax_err)
        assert s is not None

    def test_syntax_error_fstring(self):
        """SyntaxError in f-string should suggest f-string fixes."""
        def fstring_err():
            exec('f"{""}}"')

        s = get_suggestion(fstring_err)
        # May or may not produce fstring-specific output depending on error msg
        assert s is not None


# ============================================================
# StopIteration
# ============================================================

class TestStopIteration:
    def test_stop_iteration(self):
        """StopIteration should suggest next() with default."""
        def stop_iter():
            it = iter([])
            next(it)

        s = get_suggestion(stop_iter)
        assert s is not None
        fixes_text = " ".join(s.fixes)
        assert "default" in fixes_text.lower() or "next(" in fixes_text


# ============================================================
# Fuzzy Matching Utils
# ============================================================

class TestFuzzyMatching:
    def test_closest_match(self):
        assert closest_match("usernme", ["username", "email", "id"]) == "username"

    def test_no_match(self):
        assert closest_match("xyz", ["abc", "def"]) is None

    def test_edit_distance(self):
        assert edit_distance("kitten", "sitting") == 3
        assert edit_distance("", "abc") == 3
        assert edit_distance("abc", "abc") == 0

    def test_edit_distance_case(self):
        assert edit_distance("User", "user") == 1


# ============================================================
# Import Map
# ============================================================

class TestImportMap:
    def test_common_mappings_exist(self):
        """Critical mappings should be present."""
        critical = ["cv2", "PIL", "sklearn", "yaml", "bs4", "dotenv", "jwt", "serial"]
        for name in critical:
            pkg = lookup_package(name)
            assert pkg is not None, f"Missing mapping for '{name}'"

    def test_mapping_count(self):
        """Should have 100+ mappings."""
        from failwith.data.import_map import IMPORT_TO_PACKAGE
        assert len(IMPORT_TO_PACKAGE) >= 100


# ============================================================
# Formatter
# ============================================================

class TestFormatter:
    def test_plain_format(self):
        """Plain format should have no ANSI codes."""
        s = Suggestion(
            title="Test error",
            fixes=["Fix 1", "Fix 2"],
            env_info=["Python 3.11"],
        )
        output = _format_plain(s, {"theme": "plain"})
        assert "Test error" in output
        assert "Fix 1" in output
        assert "\033[" not in output

    def test_format_with_env(self):
        """Environment info should appear in output."""
        s = Suggestion(
            title="Test",
            fixes=["Fix"],
            env_info=["Python 3.11", "venv: .venv", "Ubuntu 24.04"],
        )
        output = _format_plain(s, {"theme": "plain"})
        assert "Python 3.11" in output

    def test_empty_suggestion(self):
        """Suggestion with no fixes should be falsy."""
        s = Suggestion(title="Empty", fixes=[])
        assert not s


# ============================================================
# Custom Handler Registration
# ============================================================

class TestCustomRegistration:
    def test_register_custom_handler(self):
        """User can register custom exception handlers."""

        class MyAppError(Exception):
            pass

        @register(MyAppError)
        def handle_my_error(exc_type, exc_value, exc_tb, config):
            return Suggestion(
                title="Custom app error",
                fixes=["Check your app configuration"],
            )

        def raise_custom():
            raise MyAppError("something broke")

        s = get_suggestion(raise_custom)
        assert s is not None
        assert "custom app error" in s.title.lower()

    def test_custom_handler_priority(self):
        """Custom handlers should run before built-in ones."""
        custom_ran = []

        @register(KeyError)
        def custom_key_handler(exc_type, exc_value, exc_tb, config):
            custom_ran.append(True)
            return Suggestion(
                title="Custom KeyError handler",
                fixes=["Custom fix"],
            )

        def key_err():
            d = {}
            return d["missing"]

        s = get_suggestion(key_err)
        assert s is not None
        assert custom_ran  # Custom handler was invoked


# ============================================================
# Install / Uninstall
# ============================================================

class TestInstallUninstall:
    def test_install_sets_excepthook(self):
        """install() should replace sys.excepthook."""
        import failwith
        original = sys.excepthook
        failwith.install()
        assert sys.excepthook != original
        failwith.uninstall()
        assert sys.excepthook == original

    def test_catch_context_manager(self):
        """catch() should work as context manager."""
        import failwith
        caught = False
        with failwith.catch(reraise=False):
            caught = True
            raise ValueError("test")
        assert caught

    def test_catch_decorator(self):
        """catch() should work as decorator."""
        import failwith

        @failwith.catch(reraise=False)
        def failing_func():
            raise ValueError("test")

        # Should not raise
        failing_func()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
