"""GNU ``.mo`` files, standard library only (tasks 3.4 and 6.2).

:func:`write` is the ``.mo`` writer of ``caen translate gettext``; :func:`read_po` reads back the
``.po`` that command writes, so ``tools/setup.py`` can build the wheel's ``.mo`` from the
committed ``.po`` without ``upstream/`` and without importing the package (ADR-020).
"""

from __future__ import annotations

import ast
import struct

MAGIC = 0x950412DE


def write(pairs: list[tuple[str, str]]) -> bytes:
    """``.mo`` (little endian, no hash table) of ``(msgid, msgstr)`` pairs, header included."""
    pairs = sorted(pairs, key=lambda p: p[0].encode("utf-8"))
    ids = [k.encode("utf-8") for k, _ in pairs]
    strs = [v.encode("utf-8") for _, v in pairs]
    count = len(pairs)
    start = 7 * 4 + 2 * 8 * count  # magic..hash offset, then the two tables
    id_blob = b"".join(i + b"\0" for i in ids)
    str_blob = b"".join(s + b"\0" for s in strs)
    table: list[int] = []
    offset = start
    for i in ids:
        table += [len(i), offset]
        offset += len(i) + 1
    offset = start + len(id_blob)
    for s in strs:
        table += [len(s), offset]
        offset += len(s) + 1
    head = struct.pack("<7I", MAGIC, 0, count, 28, 28 + 8 * count, 0, start)
    return head + struct.pack(f"<{len(table)}I", *table) + id_blob + str_blob


def read_po(text: str) -> list[tuple[str, str]]:
    """``(msgid, msgstr)`` pairs of a ``.po`` without contexts or plurals, header included."""
    pairs: list[tuple[str, str]] = []
    current: dict[str, str] = {}
    keyword = ""

    def flush() -> None:
        if current:
            pairs.append((current["msgid"], current["msgstr"]))
            current.clear()

    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(('msgid "', 'msgstr "')):
            keyword, _, line = line.partition(" ")
            if keyword == "msgid":
                flush()
            current[keyword] = ""
        elif not line.startswith('"') or not keyword:
            raise ValueError(f"line {number}: unsupported .po syntax: {line[:40]!r}")
        current[keyword] += ast.literal_eval(line)
    flush()
    return pairs
