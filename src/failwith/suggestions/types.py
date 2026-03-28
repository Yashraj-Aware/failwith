"""
Suggestion handlers for TypeError, KeyError, AttributeError, NameError,
ValueError, IndexError, ZeroDivisionError.
"""

from __future__ import annotations

import re
import inspect
from typing import Any, Optional, Type

from failwith.suggestions import Suggestion, register_builtin
from failwith.utils.fuzzy import closest_matches, edit_distance


def _get_locals_from_tb(exc_tb: Any) -> dict:
    """Extract local variables from the innermost traceback frame."""
    if exc_tb is None:
        return {}
    # Walk to the innermost frame
    while exc_tb.tb_next:
        exc_tb = exc_tb.tb_next
    return exc_tb.tb_frame.f_locals.copy()


def handle_key_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle KeyError with fuzzy matching against available keys."""
    # KeyError args[0] is the missing key
    if not exc_value.args:
        return None

    missing_key = exc_value.args[0]
    missing_str = str(missing_key)

    fixes = []
    title = f"Key '{missing_str}' not found in dict"

    # Try to find the dict in local variables
    locals_dict = _get_locals_from_tb(exc_tb)
    for var_name, var_val in locals_dict.items():
        if isinstance(var_val, dict) and missing_key not in var_val:
            available = [str(k) for k in var_val.keys()]
            if available:
                matches = closest_matches(missing_str, available, n=3)
                if matches:
                    dist = edit_distance(missing_str, matches[0])
                    fixes.append(f"Did you mean:    '{matches[0]}' (distance: {dist})")
                fixes.append(f"Available keys:  {available[:10]}")
                if len(available) > 10:
                    fixes.append(f"                 ... and {len(available) - 10} more")
                break

    fixes.append(f"Safe access:     data.get('{missing_str}', default_value)")
    fixes.append(f"Check existence: if '{missing_str}' in data: ...")

    return Suggestion(title=title, fixes=fixes)


def handle_attribute_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle AttributeError with fuzzy matching against available attributes."""
    msg = str(exc_value)

    # Parse "type 'X' has no attribute 'Y'" or "'X' object has no attribute 'Y'"
    match = re.search(
        r"(?:type\s+'([^']+)'|'([^']+)'\s+object)\s+has no attribute\s+'([^']+)'", msg
    )
    if not match:
        return Suggestion(
            title="Attribute not found",
            fixes=[f"Check spelling and that the object has the expected type"],
        )

    obj_type = match.group(1) or match.group(2)
    attr_name = match.group(3)

    fixes = []
    title = f"'{attr_name}' not found on {obj_type}"

    # Try to find the object and its available attributes
    locals_dict = _get_locals_from_tb(exc_tb)
    for var_name, var_val in locals_dict.items():
        type_name = type(var_val).__name__
        if type_name == obj_type:
            available = [a for a in dir(var_val) if not a.startswith("_")]
            matches = closest_matches(attr_name, available, n=3)
            if matches:
                dist = edit_distance(attr_name, matches[0])
                fixes.append(f"Did you mean:  '{matches[0]}' (distance: {dist})")
                if len(matches) > 1:
                    fixes.append(f"Also similar:  {', '.join(matches[1:])}")
            break

    # Common patterns
    if attr_name == "append" and obj_type == "NoneType":
        fixes.append("A function that should return a list is returning None")
        fixes.append("Check: missing return statement? Method modifies in-place?")
    elif obj_type == "NoneType":
        fixes.append("The variable is None — a previous operation likely failed silently")
        fixes.append("Check the return value of the function that assigned this variable")
    elif attr_name == "items" and obj_type == "list":
        fixes.append("You have a list but expected a dict")
        fixes.append("For list iteration: use enumerate(x) or just iterate directly")

    fixes.append(f"Check type:    type(your_variable)  # is it really {obj_type}?")
    fixes.append(f"Inspect:       dir(your_variable)   # see all attributes")

    return Suggestion(title=title, fixes=fixes)


def handle_name_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle NameError with scope-aware suggestions."""
    msg = str(exc_value)

    match = re.search(r"name '([^']+)' is not defined", msg)
    if not match:
        return None

    name = match.group(1)
    fixes = []
    title = f"Name '{name}' is not defined"

    # Check locals and globals for similar names
    locals_dict = _get_locals_from_tb(exc_tb)
    available = list(locals_dict.keys())

    # Also check globals from the frame
    if exc_tb:
        tb = exc_tb
        while tb.tb_next:
            tb = tb.tb_next
        available.extend(tb.tb_frame.f_globals.keys())

    # Also check builtins
    import builtins
    builtin_names = dir(builtins)

    all_names = list(set(available + builtin_names))
    matches = closest_matches(name, [n for n in all_names if not n.startswith("_")], n=3)

    if matches:
        fixes.append(f"Did you mean:  '{matches[0]}'")

    # Common patterns
    if name[0].isupper():
        fixes.append(f"Missing import? Try: from <module> import {name}")
    else:
        fixes.append(f"Variable '{name}' may not be defined yet at this point")
        fixes.append(f"Check: typo? Wrong scope? Defined in a different branch?")

    return Suggestion(title=title, fixes=fixes)


def handle_type_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle TypeError with common pattern suggestions."""
    msg = str(exc_value)
    fixes = []

    # String + int concatenation
    if "can only concatenate str" in msg and "int" in msg:
        title = "Tried to concatenate str + int"
        locals_dict = _get_locals_from_tb(exc_tb)
        fixes.extend([
            "Convert explicitly: str(your_int) + your_str",
            "Or use f-string:    f\"{your_str}{your_int}\"",
        ])

    # Not callable
    elif "is not callable" in msg:
        match = re.search(r"'(\w+)' object is not callable", msg)
        obj_type = match.group(1) if match else "object"
        title = f"'{obj_type}' is not callable"
        fixes.extend([
            "You're using () on something that isn't a function/class",
            "Common causes: variable shadows a function name, or you used () instead of []",
        ])

    # Wrong argument count
    elif "argument" in msg and ("takes" in msg or "got" in msg):
        title = "Wrong number of arguments"
        fixes.extend([
            msg,  # The original message is usually clear here
            "Check the function signature and the number of arguments you're passing",
            "Did you forget 'self' in a method definition?",
        ])

    # NoneType issues
    elif "'NoneType'" in msg:
        title = "Operation on None value"
        fixes.extend([
            "A variable is None when you expected it to have a value",
            "Common causes: function with no return, failed lookup, uninitialized variable",
            "Debug: add a check → if variable is None: raise ValueError('...')",
        ])

    # Not subscriptable
    elif "not subscriptable" in msg:
        match = re.search(r"'(\w+)' object is not subscriptable", msg)
        obj_type = match.group(1) if match else "object"
        title = f"Cannot use [] on '{obj_type}'"
        fixes.extend([
            f"'{obj_type}' doesn't support indexing with []",
            "Make sure the variable contains a list, dict, or string",
            "Check: type(your_variable) to verify the type",
        ])

    # Not iterable
    elif "not iterable" in msg:
        match = re.search(r"'(\w+)' object is not iterable", msg)
        obj_type = match.group(1) if match else "object"
        title = f"Cannot iterate over '{obj_type}'"
        fixes.extend([
            f"'{obj_type}' doesn't support iteration (for loops, list(), etc.)",
            "If it's a number, did you mean: range(n)?",
            "If None: a function probably didn't return what you expected",
        ])

    else:
        title = "Type error"
        fixes.append(msg)
        fixes.append("Check the types of your variables match what the operation expects")

    return Suggestion(title=title, fixes=fixes)


def handle_value_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle ValueError."""
    msg = str(exc_value)
    fixes = []

    # int() conversion
    if "invalid literal for int()" in msg:
        match = re.search(r"'([^']*)'", msg)
        val = match.group(1) if match else "?"
        title = f"Cannot convert '{val}' to int"
        fixes.extend([
            "The string contains non-numeric characters",
            "Strip whitespace:    int(value.strip())",
            "Handle floats:       int(float(value))",
            "Check before convert: value.isdigit() or value.lstrip('-').isdigit()",
        ])

    # Unpacking
    elif "not enough values to unpack" in msg or "too many values to unpack" in msg:
        title = "Unpacking mismatch"
        fixes.extend([
            msg,
            "The number of variables doesn't match the number of values",
            "Debug: print(len(your_iterable)) to check the count",
            "Use * to capture extra: a, b, *rest = iterable",
        ])

    else:
        title = "Invalid value"
        fixes.append(msg)
        fixes.append("The value is the right type but wrong content")
        fixes.append("Check the function's documentation for valid inputs")

    return Suggestion(title=title, fixes=fixes)


def handle_index_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle IndexError with collection size context."""
    msg = str(exc_value)
    fixes = []
    title = "Index out of range"

    # Try to find the list and index from locals
    locals_dict = _get_locals_from_tb(exc_tb)
    for var_name, var_val in locals_dict.items():
        if isinstance(var_val, (list, tuple)):
            length = len(var_val)
            fixes.append(f"'{var_name}' has {length} items (valid indices: 0 to {length - 1})")
            break

    fixes.extend([
        "Remember: Python uses 0-based indexing",
        "Last item:  my_list[-1]",
        "Safe access: my_list[i] if i < len(my_list) else default",
        "Check:       len(my_list) before accessing",
    ])

    return Suggestion(title=title, fixes=fixes)


def handle_zero_division(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle ZeroDivisionError."""
    locals_dict = _get_locals_from_tb(exc_tb)
    fixes = []
    title = "Division by zero"

    # Find variables that are 0
    zeros = [f"'{k}' = 0" for k, v in locals_dict.items()
             if isinstance(v, (int, float)) and v == 0
             and not k.startswith("_")]
    if zeros:
        fixes.append(f"Zero-valued vars: {', '.join(zeros[:5])}")

    fixes.extend([
        "Guard against zero: if divisor != 0: result = x / divisor",
        "Or use a default:   result = x / divisor if divisor else 0",
        "For safe division:  result = x / max(divisor, 1)",
    ])

    return Suggestion(title=title, fixes=fixes)


# Register handlers
register_builtin(KeyError, handle_key_error)
register_builtin(AttributeError, handle_attribute_error)
register_builtin(NameError, handle_name_error)
register_builtin(TypeError, handle_type_error)
register_builtin(ValueError, handle_value_error)
register_builtin(IndexError, handle_index_error)
register_builtin(ZeroDivisionError, handle_zero_division)
