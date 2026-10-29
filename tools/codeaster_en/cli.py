"""``caen`` command-line interface.

Implemented so far: ``caen validate`` (glossary, messages, synonyms, commands),
``caen extract catalog|messages|astest-index|inventory`` and
``caen translate command|messages``. The other groups and commands are stubs that name the
PLAN.md task which will fill them in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from codeaster_en import __version__
from codeaster_en.extract import astest as astest_extractor
from codeaster_en.extract import catalog as catalog_extractor
from codeaster_en.extract import inventory as inventory_extractor
from codeaster_en.extract import messages as messages_extractor
from codeaster_en.translate import command as command_drafts
from codeaster_en.translate import messages as messages_translate
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


@extract_app.command("inventory")
def extract_inventory(
    out: Annotated[
        Path | None,
        typer.Option(help="Inventory file to update (default: docs/INVENTORY.md)."),
    ] = None,
) -> None:
    """Rewrite the generated block of docs/INVENTORY.md (tier coverage, astest top 50)."""
    root = _repo_root()
    try:
        path = inventory_extractor.write(root, out)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        typer.echo(f"extract inventory: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"extract inventory: updated {path}")


translate_app = typer.Typer(
    help="Draft English command references; glossary-locked translation of messages and docs.",
    no_args_is_help=True,
)
app.add_typer(translate_app, name="translate")


@translate_app.command("command")
def translate_command(
    command: Annotated[
        list[str] | None,
        typer.Argument(help="Commands to draft, e.g. AFFE_MODELE."),
    ] = None,
    tier: Annotated[
        str | None,
        typer.Option(help="Draft every command of this docs/COMMAND-SET.md tier (e.g. 1)."),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option(help="Output directory (default: en/commands in the repo root)."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(help="Overwrite references whose status is not 'machine'."),
    ] = False,
    all_keywords: Annotated[
        bool,
        typer.Option(help="Expand every factor keyword, not only the key ones."),
    ] = False,
    list_untranslated: Annotated[
        bool,
        typer.Option(
            help="Print the catalog fr= strings with no en/catalog-help.yaml entry; write nothing."
        ),
    ] = False,
) -> None:
    """Write a first-draft en/commands/<CMD>.md (status: machine) from the extracted .json."""
    root = _repo_root()
    try:
        src = command_drafts.load_sources(root)
        names = command_drafts.resolve(src, command, tier)
        if list_untranslated:
            missing = command_drafts.untranslated(src, names, all_keywords)
            for fr in missing:
                typer.echo(fr)
            typer.echo(f"translate command: {len(missing)} untranslated string(s)", err=True)
            return
        outcomes = command_drafts.write(
            src, names, out or root / COMMANDS_RELPATH, force=force, all_keywords=all_keywords
        )
    except (OSError, ValueError, command_drafts.DraftError) as exc:
        typer.echo(f"translate command: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    for outcome in outcomes:
        if outcome.action == "skipped":
            typer.echo(f"translate command: skipped {outcome.command}: {outcome.reason}", err=True)
    counts = {a: sum(o.action == a for o in outcomes) for a in ("written", "unchanged", "skipped")}
    typer.echo(
        "translate command: "
        + ", ".join(f"{n} {action}" for action, n in counts.items())
        + f" ({len(outcomes)} command(s))"
    )


@translate_app.command("messages")
def translate_messages(
    family: Annotated[
        list[str] | None,
        typer.Option("--family", "-f", help="Message family, e.g. MODELISA8 (repeatable)."),
    ] = None,
    all_families: Annotated[
        bool, typer.Option("--all", help="Every family in en/messages.")
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(help="Print batches, token and cost estimate; call nothing, write nothing."),
    ] = False,
    seed_po: Annotated[
        bool,
        typer.Option(
            help="First fill messages whose French is verbatim in upstream's en-US .po "
            "(method machine, no model call)."
        ),
    ] = False,
    seed_only: Annotated[
        bool, typer.Option(help="Only the --seed-po step: no model, no --responses.")
    ] = False,
    responses: Annotated[
        Path | None,
        typer.Option(help="Take answers from this JSON Lines file instead of the Claude API."),
    ] = None,
    export_requests: Annotated[
        Path | None,
        typer.Option(help="Append the requests to this JSON Lines file; call nothing."),
    ] = None,
    model: Annotated[str, typer.Option(help="Claude model ID.")] = messages_translate.DEFAULT_MODEL,
    effort: Annotated[
        str, typer.Option(help="low | medium | high | xhigh | max.")
    ] = messages_translate.DEFAULT_EFFORT,
    batch_size: Annotated[
        int, typer.Option(min=1, help="Messages per request.")
    ] = messages_translate.DEFAULT_BATCH_SIZE,
    retries: Annotated[
        int, typer.Option(min=0, help="Re-asks for items that fail validation.")
    ] = messages_translate.DEFAULT_RETRIES,
    method: Annotated[
        str,
        typer.Option(help="Recorded method: machine (batch, default) or assisted (in session)."),
    ] = "machine",
    source: Annotated[
        str | None,
        typer.Option(help="translation_source label for --responses (default: replay:<file>)."),
    ] = None,
    limit: Annotated[
        int | None, typer.Option(min=1, help="At most this many messages per family.")
    ] = None,
    force: Annotated[
        bool, typer.Option(help="Also redo translated messages (never 'reviewed' ones).")
    ] = False,
) -> None:
    """Translate message families into en/messages (glossary-locked, placeholders validated).

    Without --responses, --dry-run or --export-requests this calls the Claude API and spends
    API credit (credentials from the environment, e.g. ANTHROPIC_API_KEY).
    """
    root = _repo_root()
    seed_po = seed_po or seed_only
    try:
        src = messages_translate.load_sources(root)
        names = messages_translate.all_families(root) if all_families else (family or [])
        if not names:
            raise messages_translate.TranslateError("give --family F (repeatable) or --all")
        if dry_run or export_requests:
            totals = [0, 0, 0, 0, 0.0]
            for name in names:
                if export_requests:
                    messages_translate.export_requests(
                        src, name, export_requests, batch_size, force, seed_po, limit
                    )
                est = messages_translate.estimate(
                    src, name, model, batch_size, force, seed_po, limit
                )
                cost = "n/a" if est.cost_usd is None else f"${est.cost_usd:.2f}"
                typer.echo(
                    f"{est.family}: {est.items} message(s), {est.requests} request(s), "
                    f"~{est.input_tokens} input / ~{est.output_tokens} output tokens, {cost}"
                )
                totals[0] += est.items
                totals[1] += est.requests
                totals[2] += est.input_tokens
                totals[3] += est.output_tokens
                totals[4] += est.cost_usd or 0.0
            typer.echo(
                f"translate messages: {len(names)} family file(s), {totals[0]} message(s), "
                f"{totals[1]} request(s), ~{totals[2]} input / ~{totals[3]} output tokens, "
                f"~${totals[4]:.2f} with {model} (estimate: chars/"
                f"{messages_translate.CHARS_PER_TOKEN:g}, no thinking tokens, no re-asks)"
            )
            if export_requests:
                typer.echo(f"translate messages: requests appended to {export_requests}")
            return
        translator: messages_translate.Translator | None = None
        if responses:
            translator = messages_translate.ReplayTranslator(responses, source)
        elif not seed_only:
            translator = messages_translate.AnthropicTranslator(model=model, effort=effort)
        failed = 0
        for name in names:
            rep = messages_translate.translate_family(
                src,
                name,
                translator,
                batch_size=batch_size,
                retries=retries,
                method=method,
                seed_po=seed_po,
                force=force,
                limit=limit,
            )
            for msg_id, problems in rep.failed.items():
                typer.echo(f"{msg_id}: not translated: {'; '.join(problems)}", err=True)
            failed += len(rep.failed)
            extra = f", glossary +{len(rep.glossary_added)}" if rep.glossary_added else ""
            typer.echo(
                f"{rep.family}: {rep.seeded} seeded, {rep.translated}/{rep.pending} translated, "
                f"{len(rep.failed)} failed, {rep.requests} request(s), "
                f"{rep.input_tokens} input / {rep.output_tokens} output tokens{extra}"
            )
    except (OSError, ValueError, messages_translate.TranslateError) as exc:
        typer.echo(f"translate messages: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    if failed:
        raise typer.Exit(code=1)


@translate_app.command("doc")
def translate_doc() -> None:
    """Chunked translation of a U4 document [not implemented yet: task 5.2]."""
    typer.echo("caen translate doc: not implemented yet (PLAN.md task 5.2).", err=True)
    raise typer.Exit(code=2)


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
