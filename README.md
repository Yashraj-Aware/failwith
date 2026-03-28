# failwith 

**Actionable error intelligence for Python.**

When Python tells you *what* broke, `failwith` tells you *why* and *how to fix it*.

```
pip install failwith
```

## Quick Start

```python
import failwith
failwith.install()
```

That's it. Every unhandled exception now gets actionable fix suggestions appended below the standard traceback.

## What It Looks Like

```
Traceback (most recent call last):
  File "app.py", line 3, in <module>
    import cv2
ModuleNotFoundError: No module named 'cv2'

┌─ 💡 failwith ─────────────────────────────────────────────────┐
│                                                                │
│  'cv2' is from the 'opencv-python' package (import ≠ package)  │
│                                                                │
│  → Install it:    pip install opencv-python                    │
│  → Or headless:   pip install opencv-python-headless           │
│  → Active venv:   .venv                                        │
│                                                                │
│  🔍 Python 3.11.5 | venv: .venv | Ubuntu 24.04               │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Features

### 1. 200+ Import Name → Package Name Mappings

`cv2` → `opencv-python`, `PIL` → `Pillow`, `sklearn` → `scikit-learn`, `yaml` → `PyYAML`, and 200+ more. Never Google "pip install what?" again.

###  Context-Aware Suggestions

Not pattern matching — actual context analysis. When a `ConnectionRefusedError` hits on port 5432, failwith knows that's PostgreSQL and suggests the right start command for your OS.

### 2. Fuzzy Matching for Typos

`KeyError`, `AttributeError`, and `NameError` get fuzzy-matched against available keys, attributes, and names. "Did you mean 'username'?" with edit distance.

### 3. File System Intelligence

`FileNotFoundError` shows similar files in the directory, current working directory, and the closest existing parent path. `PermissionError` shows file ownership and suggests `chmod`/`chown` commands.

### 4. Environment Diagnostics

Every suggestion includes Python version, venv status, and OS — the three things you always need when debugging.

### 5. Zero Dependencies

Uses only the Python standard library. No `rich`, no `click`, nothing. Zero friction to adopt.

### 6. Never Makes Things Worse

If failwith itself encounters an error, it silently degrades. Your original traceback is always printed first, unmodified.

## Supported Error Types (v0.1)

| Error | What failwith adds |
|-------|-------------------|
| `ModuleNotFoundError` | Correct `pip install` command, import↔package mapping |
| `ImportError` | Fuzzy name matching, circular import detection |
| `ConnectionRefusedError` | Service name, start commands, Docker suggestions |
| `TimeoutError` | Network debugging commands |
| `ConnectionResetError` | Server-side investigation suggestions |
| `FileNotFoundError` | Similar files, directory listing, working dir |
| `PermissionError` | File owner, chmod/chown commands |
| `KeyError` | Fuzzy match against available keys, `.get()` suggestion |
| `AttributeError` | Fuzzy match against attributes, NoneType detection |
| `NameError` | Scope-aware fuzzy matching, import suggestions |
| `TypeError` | Type mismatch fixes (str+int, not callable, etc.) |
| `ValueError` | Conversion fixes, unpacking mismatch |
| `IndexError` | Collection size context, safe access |
| `ZeroDivisionError` | Zero-valued variable identification |
| `UnicodeDecodeError` | Encoding suggestions, chardet recommendation |
| `UnicodeEncodeError` | Encoding alternatives, error handling modes |
| `RecursionError` | Recursion limit, call chain, base case reminder |
| `MemoryError` | Memory optimization strategies |
| `SyntaxError` | Common fix patterns (missing colon, Python 2→3) |
| `JSONDecodeError` | Error position context, common JSON issues |
| `StopIteration` | `next()` with default, iterator re-creation |
| `OSError` | Disk space, file descriptor limits, port conflicts |

## Advanced Usage

### Context Manager

```python
with failwith.catch(reraise=False):
    risky_operation()
```

### Decorator

```python
@failwith.catch()
def my_function():
    risky_operation()
```

### Custom Suggestions

```python
@failwith.register(MyDatabaseError)
def handle_db_error(exc_type, exc_value, exc_tb, config):
    return failwith.Suggestion(
        title="Database connection failed",
        fixes=[
            "Check DATABASE_URL in your .env file",
            "Run: docker-compose up -d postgres",
        ],
    )
```

### Configuration

```python
failwith.install(
    theme="dark",           # "dark" | "light" | "minimal" | "plain"
    show_locals=False,      # show local variable values
    max_suggestions=3,      # limit suggestions shown
)
```

## Environment Variables

| Variable | Effect |
|----------|--------|
| `NO_COLOR` | Disable colors (standard) |
| `FAILWITH_NO_COLOR` | Disable colors |
| `FAILWITH_FORCE_COLOR` | Force colors even in non-TTY |

## Contributing

Contributions are welcome! The most impactful way to contribute:

1. **Add import mappings** — edit `src/failwith/data/import_map.py`
2. **Improve suggestions** — edit handlers in `src/failwith/suggestions/`
3. **Add test cases** — real-world error scenarios in `tests/`

```bash
git clone https://github.com/yashraj/failwith.git
cd failwith
pip install -e ".[dev]"
pytest
```

## License

MIT
