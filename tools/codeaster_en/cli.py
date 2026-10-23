"""``caen`` command-line interface.

Only ``caen validate glossary`` is implemented so far; the other groups are stubs that name
the PLAN.md task which will fill them in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from codeaster_en import __version__
from codeaster_en.validate import glossary as glossary_validator

app = typer.Typer(
    help="English overlay tooling for code_aster.",
    no_args_is_help=True,
    add_completion=False,
)

GLOSSARY_RELPATH = Path("en/glossary.yaml")


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


app.add_typer(
    _stub("extract", "1.2-1.4", "Extract catalogs, messages and the astest index from upstream/."),
    name="extract",
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


def _validate_glossary(path: Path) -> bool:
    issues = glossary_validator.validate(path)
    for issue in issues:
        typer.echo(f"{path}: {issue}", err=True)
    if issues:
        typer.echo(f"glossary: {len(issues)} problem(s) in {path}", err=True)
        return False
    entries = glossary_validator.load(path)
    typer.echo(f"glossary: OK ({len(entries)} entries)")
    return True


@validate_app.callback(invoke_without_command=True)
def validate_all(ctx: typer.Context) -> None:
    """Run every available validator when no sub-command is given."""
    if ctx.invoked_subcommand is not None:
        return
    root = _repo_root()
    ok = _validate_glossary(root / GLOSSARY_RELPATH)
    raise typer.Exit(code=0 if ok else 1)


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
