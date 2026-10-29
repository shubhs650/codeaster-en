"""Where the overlay data lives: the repository checkout or the installed wheel (task 6.2).

In a checkout (editable install, tests, CI) the data is the repository's own ``en/`` and
``UPSTREAM_VERSION``, so an edit is seen at once. A wheel carries a copy under
``codeaster_en/_data/`` (staged by ``tools/setup.py``, ADR-020), plus the gettext ``.mo``
built from ``en/messages/codeaster_en.po``. Only paths are resolved here; every file is read
by the module that needs it, when it needs it.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

PACKAGE_DATA = Path(__file__).resolve().parent / "_data"
CHECKOUT = Path(__file__).resolve().parents[2]
GLOSSARY_RELPATH = Path("en/glossary.yaml")


@cache
def root() -> Path:
    """Directory holding ``en/`` and ``UPSTREAM_VERSION``: the checkout first, else the wheel."""
    if (CHECKOUT / GLOSSARY_RELPATH).is_file():
        return CHECKOUT
    return PACKAGE_DATA


def en_dir() -> Path:
    return root() / "en"


def commands_dir() -> Path:
    return en_dir() / "commands"


def messages_dir() -> Path:
    return en_dir() / "messages"


def glossary_path() -> Path:
    return root() / GLOSSARY_RELPATH


def localedir() -> Path | None:
    """Locale directory holding ``en/LC_MESSAGES/aster_messages.mo``; wheel only.

    A checkout has no ``.mo`` (it is never committed): build one with
    ``caen translate gettext --mo <localedir>`` (docs/ENGLISH-LOCALE.md).
    """
    path = PACKAGE_DATA / "locale"
    return path if path.is_dir() else None


def upstream_version() -> str | None:
    """The pinned upstream tag, first non-comment line of ``UPSTREAM_VERSION``."""
    path = root() / "UPSTREAM_VERSION"
    if not path.is_file():
        return None
    lines = (ln.strip() for ln in path.read_text().splitlines())
    return next((ln for ln in lines if ln and not ln.startswith("#")), None)
