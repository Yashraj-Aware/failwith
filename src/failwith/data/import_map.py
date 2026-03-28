"""
Mapping of Python import names to PyPI package names.

This is one of failwith's core differentiators — a curated database of
cases where `import X` requires `pip install Y` (and X != Y).

Community contributions welcome!
"""

# import_name -> (pip_package_name, optional_notes)
IMPORT_TO_PACKAGE: dict = {
    # === Computer Vision & Image Processing ===
    "cv2": ("opencv-python", "Use opencv-python-headless for server environments"),
    "PIL": ("Pillow", None),
    "skimage": ("scikit-image", None),

    # === Machine Learning & Data Science ===
    "sklearn": ("scikit-learn", None),
    "xgboost": ("xgboost", None),
    "lightgbm": ("lightgbm", None),
    "catboost": ("catboost", None),
    "tf": ("tensorflow", "Import as: import tensorflow as tf"),
    "torch": ("pytorch", "Install via: pip install torch (from pytorch.org for GPU)"),

    # === Web & API ===
    "bs4": ("beautifulsoup4", None),
    "flask_cors": ("Flask-Cors", None),
    "flask_sqlalchemy": ("Flask-SQLAlchemy", None),
    "flask_migrate": ("Flask-Migrate", None),
    "flask_login": ("Flask-Login", None),
    "flask_wtf": ("Flask-WTF", None),
    "flask_mail": ("Flask-Mail", None),
    "flask_restful": ("Flask-RESTful", None),
    "rest_framework": ("djangorestframework", None),
    "corsheaders": ("django-cors-headers", None),
    "celery": ("celery", None),
    "starlette": ("starlette", None),
    "httpx": ("httpx", None),

    # === YAML / Config ===
    "yaml": ("PyYAML", None),
    "toml": ("toml", "Built-in from Python 3.11+ as tomllib"),
    "dotenv": ("python-dotenv", None),

    # === Database ===
    "psycopg2": ("psycopg2-binary", "Use psycopg2-binary for easier install"),
    "MySQLdb": ("mysqlclient", None),
    "pymysql": ("PyMySQL", None),
    "bson": ("pymongo", "bson is included in pymongo"),
    "motor": ("motor", None),
    "redis": ("redis", None),
    "sqlalchemy": ("SQLAlchemy", None),
    "peewee": ("peewee", None),
    "alembic": ("alembic", None),

    # === Serialization & Data Formats ===
    "msgpack": ("msgpack", None),
    "ujson": ("ujson", None),
    "orjson": ("orjson", None),
    "avro": ("avro-python3", None),
    "google.protobuf": ("protobuf", None),
    "thrift": ("thrift", None),
    "xmltodict": ("xmltodict", None),

    # === Crypto & Security ===
    "Crypto": ("pycryptodome", "Not pycrypto (deprecated)"),
    "Cryptodome": ("pycryptodome", None),
    "jwt": ("PyJWT", "Not python-jwt"),
    "nacl": ("PyNaCl", None),
    "bcrypt": ("bcrypt", None),
    "paramiko": ("paramiko", None),
    "OpenSSL": ("pyOpenSSL", None),

    # === Utilities ===
    "attr": ("attrs", None),
    "attrs": ("attrs", None),
    "dateutil": ("python-dateutil", None),
    "tz": ("python-dateutil", "from dateutil import tz"),
    "decouple": ("python-decouple", None),
    "magic": ("python-magic", None),
    "slugify": ("python-slugify", None),
    "tqdm": ("tqdm", None),
    "click": ("click", None),
    "rich": ("rich", None),
    "typer": ("typer", None),
    "pydantic": ("pydantic", None),
    "arrow": ("arrow", None),
    "pendulum": ("pendulum", None),
    "humanize": ("humanize", None),

    # === Hardware & Serial ===
    "serial": ("pyserial", None),
    "usb": ("pyusb", None),
    "hid": ("hidapi", None),
    "evdev": ("evdev", None),
    "gpio": ("RPi.GPIO", "For Raspberry Pi"),

    # === GUI ===
    "wx": ("wxPython", None),
    "gi": ("PyGObject", None),
    "tkinter": ("tk", "Usually comes with Python. Try: sudo apt install python3-tk"),
    "PyQt5": ("PyQt5", None),
    "PyQt6": ("PyQt6", None),

    # === Testing ===
    "pytest": ("pytest", None),
    "mock": ("mock", "Built-in from Python 3.3+ as unittest.mock"),
    "faker": ("Faker", None),
    "factory": ("factory_boy", None),
    "hypothesis": ("hypothesis", None),
    "responses": ("responses", None),

    # === Async ===
    "aiohttp": ("aiohttp", None),
    "aiofiles": ("aiofiles", None),
    "uvloop": ("uvloop", None),
    "anyio": ("anyio", None),
    "trio": ("trio", None),

    # === Cloud & DevOps ===
    "boto3": ("boto3", None),
    "botocore": ("botocore", None),
    "google.cloud": ("google-cloud-core", None),
    "azure": ("azure-core", None),
    "docker": ("docker", None),
    "kubernetes": ("kubernetes", None),
    "fabric": ("fabric", None),

    # === NLP / Text ===
    "spacy": ("spacy", "After install, also download a model: python -m spacy download en_core_web_sm"),
    "nltk": ("nltk", "After install, also download data: python -m nltk.downloader all"),
    "gensim": ("gensim", None),
    "transformers": ("transformers", None),
    "sentence_transformers": ("sentence-transformers", None),
    "tiktoken": ("tiktoken", None),
    "langchain": ("langchain", None),

    # === Scientific ===
    "scipy": ("scipy", None),
    "sympy": ("sympy", None),
    "astropy": ("astropy", None),
    "networkx": ("networkx", None),

    # === Plotting ===
    "matplotlib": ("matplotlib", None),
    "mpl_toolkits": ("matplotlib", "Part of matplotlib"),
    "plotly": ("plotly", None),
    "seaborn": ("seaborn", None),
    "bokeh": ("bokeh", None),
    "altair": ("altair", None),

    # === Misc ===
    "lxml": ("lxml", None),
    "geopy": ("geopy", None),
    "shapely": ("Shapely", None),
    "fiona": ("Fiona", None),
    "rasterio": ("rasterio", None),
    "pyproj": ("pyproj", None),
    "unidecode": ("Unidecode", None),
    "emoji": ("emoji", None),
    "colorama": ("colorama", None),
    "termcolor": ("termcolor", None),
    "tabulate": ("tabulate", None),
    "prettytable": ("prettytable", None),
    "alive_progress": ("alive-progress", None),
    "loguru": ("loguru", None),
    "sentry_sdk": ("sentry-sdk", None),
    "stripe": ("stripe", None),
    "twilio": ("twilio", None),
    "sendgrid": ("sendgrid", None),
    "jinja2": ("Jinja2", None),
    "markupsafe": ("MarkupSafe", None),
    "wrapt": ("wrapt", None),
    "tenacity": ("tenacity", None),
    "backoff": ("backoff", None),
}


def lookup_package(import_name: str) -> tuple | None:
    """
    Look up the pip package name for a given import name.

    Returns (package_name, notes) or None if not found.
    Also handles submodule lookups (e.g., 'google.cloud.storage' -> 'google.cloud').
    """
    # Direct match
    if import_name in IMPORT_TO_PACKAGE:
        return IMPORT_TO_PACKAGE[import_name]

    # Try progressively shorter prefixes for dotted imports
    parts = import_name.split(".")
    for i in range(len(parts) - 1, 0, -1):
        prefix = ".".join(parts[:i])
        if prefix in IMPORT_TO_PACKAGE:
            return IMPORT_TO_PACKAGE[prefix]

    return None
