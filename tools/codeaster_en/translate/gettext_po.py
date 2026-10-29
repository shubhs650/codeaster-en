"""``caen translate gettext``: English messages as a gettext catalog (task 3.4, ADR-004).

``en/messages/<FAMILY>.en.json`` stays the only place English message text is edited. This
module turns it into a build artefact the solver loads itself:

- ``en/messages/codeaster_en.po``, committed and regenerated, never hand-edited (CI checks it is
  up to date through ``caen validate``);
- ``<localedir>/en/LC_MESSAGES/aster_messages.mo``, built on demand and never committed.

How the solver finds it (upstream 17.4.26, see ADR-004 and ``docs/ENGLISH-LOCALE.md``):
``DEBUT(LANG='EN')`` calls ``code_aster.Utilities.i18n.Language.translation("EN")``, which asks
``gettext.translation("aster_messages", localedir, languages=["EN", "en", ...])`` with
``localedir = $ASTER_LOCALEDIR``. The domain is ``aster_messages`` and the language directory
is ``en``.

The ``msgid`` is the French text exactly as passed to ``_()``, which is the ``fr`` field the
extractor took from the upstream source with ``ast``. Included:

- every message with an ``en`` that is not ``stale``, except the bare strings that upstream does
  not wrap in ``_()`` (``"gettext": false`` without ``fstring_names``: gettext never sees
  them) and the log-structure lines of :data:`KEEP_FRENCH`. The two f-strings (``POST0_55``/
  ``POST0_56``) are included: ``_(f"...")`` looks up the evaluated text, which is the ``fr``
  the extractor rebuilt;
- the four box footers ``Utmess.format_message`` appends to ``<A>``/``<E>``/``<S>``/``<F>``
  messages (``dcomm``), translated at call time, so they switch with ``LANG``. Their English is
  :data:`codeaster_en.mess.render.FOOTERS_EN`, so the renderer and the solver say the same.

Two messages with the same French share one ``msgid``, so they must share one English text; a
different one is an error here and in ``caen validate gettext``.

Messages carrying placeholders are flagged ``python-format``, so ``msgfmt --check-format``
verifies the English uses the same directives. The ``.mo`` writer below needs no system tool;
``msgfmt`` is used only as an extra check when it is installed (:func:`msgfmt_check`).
"""

from __future__ import annotations

import ast
import json
import shutil
import struct
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from codeaster_en.extract.messages import SUFFIX
from codeaster_en.mess.render import FOOTERS_EN

GENERATOR = "codeaster_en.translate.gettext_po"
GENERATOR_VERSION = "1"

DOMAIN = "aster_messages"  # code_aster/Utilities/i18n.py Language.set_domain
LANGUAGE = "en"  # DEBUT(LANG='EN') -> languages ["EN", "en", "en*"]
MESSAGES_RELDIR = Path("en/messages")
PO_RELPATH = MESSAGES_RELDIR / "codeaster_en.po"
MO_DEFAULT_LOCALEDIR = Path("build/locale")
UTMESS_RELPATH = Path("code_aster/Messages/Utmess.py")

# Messages left out of the catalog so the solver keeps printing their French: tools read the
# log by these lines (ADR-018). ``caen mess translate`` still renders them in English.
KEEP_FRENCH = {
    # run_aster/status.py RE_FIN counts "<I> <FIN> ARRET NORMAL" to tell a run ended normally.
    "SUPERVIS2_99": "run_aster/status.py RE_FIN",
    # Command stage structure: codeaster_en.mess.parser RE_STAGE, RE_STAGE_END, RE_MEMORY,
    # RE_DEPENDS, RE_END, and any script that greps "# Commande #" in a .mess.
    "SUPERVIS2_71": "stage header (# Commande #)",
    "SUPERVIS2_72": "stage result (# Résultat commande #)",
    "SUPERVIS2_73": "stage memory (# Mémoire (Mo))",
    "SUPERVIS2_74": "stage memory (# Mémoire (Mo))",
    "SUPERVIS2_75": "stage end (# Fin commande #)",
    "SUPERVIS2_80": "stage dependencies (# Dépend de)",
}


class CatalogError(ValueError):
    """The messages cannot be turned into one consistent catalog."""


@dataclass
class Entry:
    msgid: str
    msgstr: str
    ids: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    python_format: bool = False


def mo_path(localedir: Path) -> Path:
    """Where gettext looks for the catalog under ``localedir``."""
    return localedir / LANGUAGE / "LC_MESSAGES" / f"{DOMAIN}.mo"


def utmess_footers(upstream: Path) -> dict[str, tuple[str, int]]:
    """``{severity: (French msgid, line)}`` of the ``dcomm`` dict in ``format_message``."""
    path = upstream / UTMESS_RELPATH
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "dcomm" for t in node.targets)
            and isinstance(node.value, ast.Dict)
        ):
            found: dict[str, tuple[str, int]] = {}
            for key, value in zip(node.value.keys, node.value.values, strict=True):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Name)
                    and value.func.id == "_"
                    and len(value.args) == 1
                    and isinstance(value.args[0], ast.Constant)
                ):
                    found[key.value] = (value.args[0].value, value.lineno)
            return found
    raise CatalogError(f"{path}: no `dcomm = {{...}}` dict found")


def _family_docs(messages_dir: Path) -> list[dict]:
    docs = []
    for path in sorted(messages_dir.glob(f"*{SUFFIX}")):
        docs.append(json.loads(path.read_text(encoding="utf-8")))
    if not docs:
        raise CatalogError(f"{messages_dir}: no *{SUFFIX} files")
    return docs


def in_catalog(msg: dict) -> bool:
    """Whether a message of ``en/messages`` belongs in the gettext catalog."""
    if msg.get("gettext") is False and not msg.get("fstring_names"):
        return False  # a bare string: upstream never passes it to _()
    if msg.get("id") in KEEP_FRENCH:
        return False
    return bool(msg.get("fr")) and bool(msg.get("en")) and not msg.get("stale")


def collect(docs: list[dict], footers: dict[str, tuple[str, int]]) -> list[Entry]:
    """Catalog entries in family file order, then the footers; duplicates are merged."""
    entries: dict[str, Entry] = {}
    conflicts: list[str] = []

    def add(msgid: str, msgstr: str, ident: str, ref: str, method: str, fmt: bool) -> None:
        entry = entries.get(msgid)
        if entry is None:
            entry = entries[msgid] = Entry(msgid, msgstr, python_format=fmt)
        elif entry.msgstr != msgstr:
            conflicts.append(f"{ident}: same French as {entry.ids[0]} but different English")
            return
        entry.ids.append(ident)
        entry.refs.append(ref)
        if method not in entry.methods:
            entry.methods.append(method)

    for doc in docs:
        source = doc["source"]["file"]
        for msg in doc["messages"].values():
            if in_catalog(msg):
                ref = f"{source}:{msg['source']['line']}"
                add(msg["fr"], msg["en"], msg["id"], ref, msg["method"], bool(msg["placeholders"]))
    for severity, (fr, line) in sorted(footers.items()):
        if severity not in FOOTERS_EN:
            raise CatalogError(f"Utmess footer {severity!r} has no English in FOOTERS_EN")
        ref = f"{UTMESS_RELPATH}:{line}"
        add(fr, FOOTERS_EN[severity], f"Utmess footer {severity}", ref, "assisted", False)
    if conflicts:
        raise CatalogError("; ".join(conflicts))
    return list(entries.values())


def _quote(text: str) -> str:
    escaped = (
        text.replace("\\", "\\\\").replace('"', '\\"').replace("\t", "\\t").replace("\r", "\\r")
    )
    return '"' + escaped.replace("\n", "\\n") + '"'


def _po_string(keyword: str, text: str) -> list[str]:
    """gettext's layout: one line when short, else ``""`` then one line per ``\\n``."""
    if "\n" not in text.rstrip("\n") and len(text) < 70:
        return [f"{keyword} {_quote(text)}"]
    lines = [f'{keyword} ""']
    parts = text.split("\n")
    for i, part in enumerate(parts):
        last = i == len(parts) - 1
        if last and not part:
            break
        lines.append(_quote(part if last else part + "\n"))
    return lines


def header(provenance: dict[str, str]) -> str:
    return (
        f"Project-Id-Version: codeaster-en (code_aster {provenance['upstream']})\n"
        "Report-Msgid-Bugs-To: https://github.com/shubhs650/codeaster-en/issues\n"
        "Last-Translator: codeaster-en agents (not reviewed; see method per entry)\n"
        "Language-Team: codeaster-en\n"
        "Language: en\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=UTF-8\n"
        "Content-Transfer-Encoding: 8bit\n"
        "Plural-Forms: nplurals=2; plural=(n != 1);\n"
    )


def render_po(entries: list[Entry], provenance: dict[str, str]) -> str:
    out = [
        "# English messages for code_aster, gettext domain 'aster_messages' (ADR-004).",
        "# GENERATED by `caen translate gettext` from en/messages/*.en.json: do not edit;",
        "# change the JSON and regenerate. Install: docs/ENGLISH-LOCALE.md.",
        f"# Upstream: code_aster {provenance['upstream']} ({provenance['upstream_commit']}).",
        f"# Generator: {GENERATOR} {GENERATOR_VERSION}.",
        "# Methods: machine = upstream 2016 .po seed; assisted = agent translation, not reviewed.",
        "# Copyright (C) EDF R&D (French source texts) and the codeaster-en contributors.",
        "# License: GPL-3.0-or-later.",
        "#",
        'msgid ""',
    ]
    out.extend(_po_string("msgstr", header(provenance)))
    for entry in entries:
        out.append("")
        out.append(f"#. {' '.join(entry.ids)} [{', '.join(entry.methods)}]")
        out.extend(f"#: {ref}" for ref in entry.refs)
        if entry.python_format:
            out.append("#, python-format")
        out.extend(_po_string("msgid", entry.msgid))
        out.extend(_po_string("msgstr", entry.msgstr))
    return "\n".join(out) + "\n"


def render_mo(entries: list[Entry], provenance: dict[str, str]) -> bytes:
    """GNU ``.mo`` (little endian, no hash table), the format ``gettext.GNUTranslations`` reads."""
    pairs = sorted(
        [("", header(provenance))] + [(e.msgid, e.msgstr) for e in entries],
        key=lambda p: p[0].encode("utf-8"),
    )
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
    head = struct.pack("<7I", 0x950412DE, 0, count, 28, 28 + 8 * count, 0, start)
    return head + struct.pack(f"<{len(table)}I", *table) + id_blob + str_blob


def load(repo: Path, upstream: Path | None = None) -> tuple[list[Entry], dict[str, str]]:
    """Catalog entries and provenance from ``repo``'s ``en/messages`` and ``upstream/``."""
    docs = _family_docs(repo / MESSAGES_RELDIR)
    generated = docs[0]["_generated_from"]
    provenance = {k: generated[k] for k in ("upstream", "upstream_commit")}
    footers = utmess_footers(upstream or repo / "upstream")
    return collect(docs, footers), provenance


def build(repo: Path, po: Path | None = None, localedir: Path | None = None) -> dict[str, object]:
    """Write the ``.po`` (default ``en/messages/codeaster_en.po``) and, if asked, the ``.mo``."""
    entries, provenance = load(repo)
    po = po or repo / PO_RELPATH
    po.write_text(render_po(entries, provenance), encoding="utf-8")
    result: dict[str, object] = {"po": po, "entries": len(entries), "mo": None}
    if localedir is not None:
        mo = mo_path(localedir)
        mo.parent.mkdir(parents=True, exist_ok=True)
        mo.write_bytes(render_mo(entries, provenance))
        result["mo"] = mo
    return result


def check(repo: Path) -> list[str]:
    """Problems with the committed ``.po``: missing, out of date, or messages not consistent."""
    try:
        entries, provenance = load(repo)
    except (CatalogError, OSError, KeyError, ValueError) as exc:
        return [str(exc)]
    path = repo / PO_RELPATH
    if not path.is_file():
        return [f"{path}: missing (run `caen translate gettext`)"]
    if path.read_text(encoding="utf-8") != render_po(entries, provenance):
        return [f"{path}: out of date with en/messages (run `caen translate gettext`)"]
    return []


def msgfmt_check(po: Path, mo: Path) -> str | None:
    """Run ``msgfmt --check`` when it is installed; ``None`` when it is not, else its output."""
    exe = shutil.which("msgfmt")
    if exe is None:
        return None
    proc = subprocess.run(
        [exe, "--check", "--statistics", "-o", str(mo), str(po)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise CatalogError(f"msgfmt failed on {po}:\n{proc.stderr.strip()}")
    return proc.stderr.strip()
