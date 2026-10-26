"""``caen`` command-line interface.

Implemented so far: ``caen validate`` (glossary, messages, synonyms, commands) and
``caen extract catalog|messages|astest-index``. The other groups are stubs that name the PLAN.md
task which will fill them in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from codeaster_en import __version__
from codeaster_en.extract import astest as astest_extractor
from codeaster_en.extract import catalog as catalog_extractor
from codeaster_en.extract import messages as messages_extractor
from codeaster_en.validate import commands as commands_validator
from codeaster_en.validate import glossary as glossary_validator
from codeaster_en.validate import messages as messages_validator
from codeaster_en.validate import synonyms as synonyms_validator

app = typer.Typer(
    help="English overlay tooling for code_aster.",
    no_args_is_help=True,
    add_completion=False,
)

GLOSSARY_RELPATH = Path("en/glossary.yaml")
COMMANDS_RELPATH = Path("en/commands")
MESSAGES_RELPATH = Path("en/messages")


def _repo_root(start: Path | None = None) -> Path:
    """Nearest ancestor of ``start`` (default: cwd) that contains ``en/glossary.yaml``."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / GLOSSARY_RELPATH).is_file():
            return candidate
    return here


def _stub(name: str, task: str, help_text: str) -> typer.Typer:
    group = typer.Typer(help=f"{help_text} [not implemented yet: task {task}]")

    @group.callback(invoke_without_command=True)
    def _not_implemented(ctx: typer.Context) -> None:
        if ctx.invoked_subcommand is None:
            typer.echo(f"caen {name}: not implemented yet (PLAN.md task {task}).", err=True)
            raise typer.Exit(code=2)

    return group


extract_app = typer.Typer(
    help="Extract catalogs, messages and the astest index from upstream/.",
    no_args_is_help=True,
)
app.add_typer(extract_app, name="extract")


@extract_app.command("catalog")
def extract_catalog(
    command: Annotated[
        list[str] | None,
        typer.Argument(help="Only these commands (default: all)."),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option(help="Output directory (default: en/commands in the repo root)."),
    ] = None,
) -> None:
    """Write en/commands/<CMD>.json for every command in upstream's catalog."""
    root = _repo_root()
    try:
        written = catalog_extractor.write(root, out or root / COMMANDS_RELPATH, command)
    except (FileNotFoundError, KeyError, RuntimeError) as exc:
        typer.echo(f"extract catalog: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"extract catalog: wrote {len(written)} command file(s)")


@extract_app.command("messages")
def extract_messages(
    family: Annotated[
        list[str] | None,
        typer.Argument(help="Only these families, e.g. MECANONLINE (default: all)."),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option(help="Output directory (default: en/messages in the repo root)."),
    ] = None,
) -> None:
    """Write en/messages/<FAMILY>.en.json for every upstream message family."""
    root = _repo_root()
    try:
        written = messages_extractor.write(root, out or root / MESSAGES_RELPATH, family)
    except (FileNotFoundError, KeyError, messages_extractor.MessageFileError) as exc:
        typer.echo(f"extract messages: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"extract messages: wrote {len(written)} family file(s)")


@extract_app.command("astest-index")
def extract_astest_index(
    out: Annotated[
        Path | None,
        typer.Option(help="Output file (default: en/astest-index.json in the repo root)."),
    ] = None,
) -> None:
    """Write en/astest-index.json: commands used by every upstream test case."""
    root = _repo_root()
    try:
        doc = astest_extractor.write(root, out or root / astest_extractor.INDEX_RELPATH)
    except FileNotFoundError as exc:
        typer.echo(f"extract astest-index: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    summary = doc["summary"]
    typer.echo(
        f"extract astest-index: {summary['testcases']} test case(s), "
        f"{summary['command_files']} command file(s), "
        f"{summary['commands_used']}/{summary['known_commands']} command(s) used"
    )


app.add_typer(
    _stub("translate", "2.2/3.1/5.2", "Glossary-locked LLM translation of commands and messages."),
    name="translate",
)
app.add_typer(_stub("mess", "4.3", "Parse a .mess log and render it in English."), name="mess")
app.add_typer(
    _stub("report", "4.6", "Generate an English engineering report from a job directory."),
    name="report",
)
app.add_typer(
    _stub("upstream", "7.1", "Bump the pinned upstream tag and diff extracted data."),
    name="upstream",
)
app.add_typer(_stub("bundle", "5.5", "Package the overlay data for ClearFEA."), name="bundle")

validate_app = typer.Typer(help="Validate overlay artefacts (glossary, placeholders, schemas).")
app.add_typer(validate_app, name="validate")


def _report(name: str, issues: list[str], ok_detail: str) -> bool:
    for issue in issues:
        typer.echo(issue, err=True)
    if issues:
        typer.echo(f"{name}: {len(issues)} problem(s)", err=True)
        return False
    typer.echo(f"{name}: OK ({ok_detail})")
    return True


def _validate_glossary(path: Path) -> bool:
    issues = glossary_validator.validate(path)
    if issues:
        return _report("glossary", [f"{path}: {issue}" for issue in issues], "")
    entries = glossary_validator.load(path)
    return _report("glossary", [], f"{len(entries)} entries")


def _validate_messages(root: Path) -> bool:
    issues, families, translated = messages_validator.validate_dir(root / MESSAGES_RELPATH)
    return _report("messages", issues, f"{families} families, {translated} translated")


def _validate_synonyms(root: Path) -> bool:
    glossary = root / GLOSSARY_RELPATH
    try:
        entries = glossary_validator.load(glossary)
    except (OSError, ValueError) as exc:
        return _report("synonyms", [f"{glossary}: cannot read: {exc}"], "")
    forbidden = synonyms_validator.aliases(entries)
    issues, files = synonyms_validator.scan_tree(root / "en", forbidden)
    return _report("synonyms", issues, f"{files} Markdown file(s), {len(forbidden)} aliases")


def _validate_commands(root: Path) -> bool:
    issues, files = commands_validator.validate_dir(root / COMMANDS_RELPATH)
    return _report("commands", issues, f"{files} reference(s)")


@validate_app.callback(invoke_without_command=True)
def validate_all(ctx: typer.Context) -> None:
    """Run every validator when no sub-command is given."""
    if ctx.invoked_subcommand is not None:
        return
    root = _repo_root()
    results = [
        _validate_glossary(root / GLOSSARY_RELPATH),
        _validate_messages(root),
        _validate_synonyms(root),
        _validate_commands(root),
    ]
    raise typer.Exit(code=0 if all(results) else 1)


@validate_app.command("glossary")
def validate_glossary(
    path: Annotated[
        Path | None,
        typer.Argument(help="Glossary file (default: en/glossary.yaml in the repo root)."),
    ] = None,
) -> None:
    """Check en/glossary.yaml: unique fr, non-empty en, valid kind, unique command en."""
    target = path or _repo_root() / GLOSSARY_RELPATH
    if not _validate_glossary(target):
        raise typer.Exit(code=1)


@validate_app.command("messages")
def validate_messages() -> None:
    """Check en/messages: ids, placeholder lists, and fr/en placeholder equality."""
    if not _validate_messages(_repo_root()):
        raise typer.Exit(code=1)


@validate_app.command("synonyms")
def validate_synonyms() -> None:
    """Scan en/**/*.md for the glossary's forbidden synonyms (aliases_en)."""
    if not _validate_synonyms(_repo_root()):
        raise typer.Exit(code=1)


@validate_app.command("commands")
def validate_commands() -> None:
    """Check that keyword tables in en/commands/*.md only name keywords in the .json."""
    if not _validate_commands(_repo_root()):
        raise typer.Exit(code=1)


def _print_version(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version", is_eager=True, callback=_print_version, help="Print the version."
        ),
    ] = False,
) -> None:
    """English overlay tooling for code_aster."""
