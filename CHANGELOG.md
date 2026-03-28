# Changelog

All notable changes to `failwith` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-03-29

### Added

- Core `failwith.install()` one-liner activation
- `failwith.catch()` context manager and decorator
- `@failwith.register()` custom suggestion handler API
- 20 built-in error type handlers:
  - `ModuleNotFoundError` with 120+ import→package name mappings
  - `ImportError` with fuzzy name matching and circular import detection
  - `ConnectionRefusedError` with port-aware service suggestions
  - `TimeoutError` and `ConnectionResetError` with network debug tips
  - `FileNotFoundError` with similar file search and directory listing
  - `PermissionError` with ownership and chmod/chown suggestions
  - `KeyError` with fuzzy matching against available keys
  - `AttributeError` with fuzzy matching and NoneType detection
  - `NameError` with scope-aware fuzzy matching
  - `TypeError` with common pattern fixes (str+int, not callable, etc.)
  - `ValueError` with conversion and unpacking suggestions
  - `IndexError` with collection size context
  - `ZeroDivisionError` with zero-valued variable identification
  - `UnicodeDecodeError` / `UnicodeEncodeError` with encoding suggestions
  - `RecursionError` with recursion limit and call chain info
  - `MemoryError` with optimization strategies
  - `SyntaxError` with common fix patterns
  - `json.JSONDecodeError` with error position context
  - `StopIteration` with next() default suggestion
  - `OSError` with errno-specific suggestions (disk full, too many files, port in use)
- Port→service mapping database (40+ common ports)
- Environment diagnostics (Python version, venv, OS detection)
- ANSI color output with graceful plain-text fallback
- Cross-platform support (Linux, macOS, Windows)
- Zero runtime dependencies
