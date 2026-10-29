"""Stage the overlay data into the wheel and the sdist (task 6.2, ADR-020).

The package lives in ``tools/`` but its data is the repository's ``en/``, which a wheel cannot
reach. ``build_py`` and ``sdist`` copy the files listed in :data:`DATA` into
``codeaster_en/_data/`` of the build tree (never of the source tree), plus the gettext ``.mo``
built from the committed ``.po``. A wheel built from the sdist finds them already in place.
Editable installs stage nothing: ``codeaster_en.data`` reads the checkout directly.
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
TARGET = Path("codeaster_en") / "_data"

# Repository files shipped as package data, as globs relative to the repository root. Left out:
# en/astest-index.json (6 MB, only the draft generator reads it) and en/guide/ (prose).
DATA = (
    "LICENSE",
    "NOTICE.md",
    "UPSTREAM_VERSION",
    "en/glossary.yaml",
    "en/catalog-help.yaml",
    "en/doc-ids.yaml",
    "en/commands/*.json",
    "en/commands/*.md",
    "en/messages/*.en.json",
    "en/messages/codeaster_en.po",
)
PO = "en/messages/codeaster_en.po"
MO = "locale/en/LC_MESSAGES/aster_messages.mo"


def _mo_module():
    spec = importlib.util.spec_from_file_location("_caen_mo", HERE / "codeaster_en/translate/mo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage(dest: Path) -> int:
    """Copy :data:`DATA` and the ``.mo`` under ``dest``; 0 when not built from a checkout."""
    if not (REPO / "en" / "glossary.yaml").is_file():
        return 0
    if dest.exists():
        shutil.rmtree(dest)
    count = 0
    for pattern in DATA:
        matches = sorted(REPO.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"package data {pattern!r} matches nothing in {REPO}")
        for src in matches:
            out = dest / src.relative_to(REPO)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, out)
            count += 1
    mo = _mo_module()
    out = dest / MO
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(mo.write(mo.read_po((REPO / PO).read_text(encoding="utf-8"))))
    return count + 1


class BuildPy(build_py):
    def run(self) -> None:
        super().run()
        if not getattr(self, "editable_mode", False):
            stage(Path(self.build_lib) / TARGET)

    def get_outputs(self, include_bytecode: bool = True) -> list[str]:
        outputs = super().get_outputs(include_bytecode)
        data = Path(self.build_lib) / TARGET
        if data.is_dir():
            outputs += [str(p) for p in data.rglob("*") if p.is_file()]
        return outputs


class Sdist(sdist):
    def make_release_tree(self, base_dir: str, files: list[str]) -> None:
        super().make_release_tree(base_dir, files)
        stage(Path(base_dir) / TARGET)


setup(cmdclass={"build_py": BuildPy, "sdist": Sdist})
