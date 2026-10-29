"""``caen`` command-line interface.

Implemented so far: ``caen validate`` (glossary, messages, synonyms, commands),
``caen extract catalog|messages|astest-index|inventory``, ``caen translate command|messages``,
``caen mess parse|translate`` and ``caen results fields|extrema|reactions|modal``. The other
groups and commands are stubs that name the PLAN.md task which will fill them in.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from codeaster_en import __version__
from codeaster_en import mess as mess_module
from codeaster_en import results as results_module
from codeaster_en.extract import astest as astest_extractor
from codeaster_en.extract import catalog as catalog_extractor
from codeaster_en.extract import inventory as inventory_extractor
from codeaster_en.extract import messages as messages_extractor
from codeaster_en.mess import render as mess_render
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


mess_app = typer.Typer(
    help="Parse a code_aster .mess log and render it in English.",
    no_args_is_help=True,
)
app.add_typer(mess_app, name="mess")


@mess_app.command("parse")
def mess_parse(
    mess: Annotated[Path, typer.Argument(help="The .mess log, e.g. output/run.mess.")],
    comm: Annotated[
        Path | None,
        typer.Option(help="The user's .comm (default: ../input/run.comm when it exists)."),
    ] = None,
    out: Annotated[
        Path | None,
        typer.Option(help="Write the events, stages, summary and classification as JSON."),
    ] = None,
    raw: Annotated[
        bool, typer.Option(help="Include the raw lines of each event in the JSON.")
    ] = True,
) -> None:
    """Parse a .mess log into events; print a summary and the failure class."""
    if not mess.is_file():
        typer.echo(f"mess parse: no such file: {mess}", err=True)
        raise typer.Exit(code=1)
    log = mess_module.parse(mess, comm=comm)
    result = mess_module.classify(log)
    summary = log.summary()
    if out is not None:
        data = log.to_dict(raw=raw)
        data["classification"] = result.to_dict()
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = ", ".join(f"{k} {v}" for k, v in sorted(summary["events"].items()))
    typer.echo(f"mess parse: {summary['lines']} lines -> {counts}")
    typer.echo(
        f"  diagnostic {summary['diagnostic_job']}, exit code {summary['exit_code']}, "
        f"errors {summary['errors'] or 'none'}, alarms {summary['alarms'] or 'none'}"
    )
    if result.failed:
        stage = summary["failed_stage"] or {}
        where = f" in {stage.get('command')} (command #{stage.get('number')})" if stage else ""
        typer.echo(f"  failure: {result.failure_class}{where}: {result.reason}")
    else:
        typer.echo("  run ended normally")


@mess_app.command("translate")
def mess_translate(
    mess: Annotated[Path, typer.Argument(help="The .mess log, e.g. output/run.mess.")],
    comm: Annotated[
        Path | None,
        typer.Option(help="The user's .comm (default: ../input/run.comm when it exists)."),
    ] = None,
    out_dir: Annotated[
        Path | None,
        typer.Option(
            help="Where to write <name>.en.mess and <name>.en.json (default: next to the log)."
        ),
    ] = None,
    messages: Annotated[
        Path | None,
        typer.Option(help="Message families to use (default: en/messages of the overlay)."),
    ] = None,
    strict: Annotated[
        bool,
        typer.Option(help="Exit 1 when a diagnostic box could not be rendered in English."),
    ] = False,
) -> None:
    """Render a .mess log in English: <name>.en.mess (the log) and <name>.en.json."""
    if not mess.is_file():
        typer.echo(f"mess translate: no such file: {mess}", err=True)
        raise typer.Exit(code=1)
    try:
        catalog = mess_render.MessageCatalog(messages)
    except FileNotFoundError as exc:
        typer.echo(f"mess translate: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    english = mess_render.translate(mess_module.parse(mess, comm=comm), catalog)
    target = out_dir or mess.parent
    target.mkdir(parents=True, exist_ok=True)
    stem = mess.name[: -len(".mess")] if mess.name.endswith(".mess") else mess.name
    text_path = target / f"{stem}.en.mess"
    json_path = target / f"{stem}.en.json"
    text_path.write_text(english.to_text(), encoding="utf-8")
    json_path.write_text(english.to_json(), encoding="utf-8")
    cov = english.coverage()
    typer.echo(f"mess translate: wrote {text_path} and {json_path}")
    typer.echo(
        f"  diagnostics in English: {cov['diagnostics_english']}/{cov['diagnostics']}"
        + (
            f" (not: {', '.join(cov['diagnostics_not_english'])})"
            if cov["diagnostics_not_english"]
            else ""
        )
    )
    if cov["untranslated_messages"]:
        typer.echo(f"  messages without English: {', '.join(cov['untranslated_messages'])}")
    for problem in english.problems():
        typer.echo(f"  {problem['headline']}")
    if strict and cov["diagnostics_not_english"]:
        raise typer.Exit(code=1)


results_app = typer.Typer(
    help="Read a run's results (.rmed and IMPR_TABLE files) with English labels.",
    no_args_is_help=True,
)
app.add_typer(results_app, name="results")

RunPath = Annotated[
    Path,
    typer.Argument(help="A .rmed file, or a job's output/ directory (run.rmed + tables/)."),
]
JsonFlag = Annotated[bool, typer.Option("--json", help="Print JSON instead of text.")]


def _open_results(path: Path) -> tuple[results_module.Results, list[results_module.Table]]:
    if path.is_dir():
        rmeds = sorted(path.glob("*.rmed")) or sorted(path.glob("*.med"))
        if not rmeds:
            typer.echo(f"results: no .rmed file in {path}", err=True)
            raise typer.Exit(code=1)
        return results_module.open(rmeds[0]), results_module.read_table_dir(path / "tables")
    if not path.is_file():
        typer.echo(f"results: no such file: {path}", err=True)
        raise typer.Exit(code=1)
    return results_module.open(path), results_module.read_table_dir(path.parent / "tables")


def _echo_json(data: object) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


def _g(value: float | None) -> str:
    return "-" if value is None else f"{value:.4g}"


@results_app.command("fields")
def results_fields(path: RunPath, as_json: JsonFlag = False) -> None:
    """List the results, fields, components and steps in a .rmed file, and its groups."""
    res, _tables = _open_results(path)
    with res:
        fields, groups = res.fields(), res.groups()
    if as_json:
        _echo_json({"fields": [f.to_dict() for f in fields], "groups": groups})
        return
    for f in fields:
        label = f" ({f.label})" if f.label else ""
        typer.echo(f"{f.result} {f.field}{label}: at {', '.join(f.locations)}")
        typer.echo(f"  components: {', '.join(f.components)}")
        steps = ", ".join(f"{s.nume_ordre} ({s.value:g})" for s in f.steps)
        typer.echo(f"  steps (NUME_ORDRE, INST or FREQ): {steps}")
    typer.echo(f"node groups: {', '.join(groups['node']) or 'none'}")
    typer.echo(f"element groups: {', '.join(groups['element']) or 'none'}")


@results_app.command("extrema")
def results_extrema(
    path: RunPath,
    field: Annotated[str, typer.Argument(help="Field name, e.g. SIEQ_NOEU or DEPL.")],
    components: Annotated[
        list[str],
        typer.Argument(help="Component, e.g. VMIS; several give their norm (DX DY DZ)."),
    ],
    group: Annotated[
        list[str] | None, typer.Option("--group", "-g", help="Group (repeatable).")
    ] = None,
    step: Annotated[int | None, typer.Option(help="NUME_ORDRE (default: the last).")] = None,
    as_json: JsonFlag = False,
) -> None:
    """Min and max of a component over the whole model and per group, with location."""
    res, _tables = _open_results(path)
    comp: str | tuple[str, ...] = components[0] if len(components) == 1 else tuple(components)
    try:
        with res:
            found = res.extrema(field, comp, groups=group or [], nume_ordre=step)
    except KeyError as exc:
        typer.echo(f"results extrema: {exc.args[0]}", err=True)
        raise typer.Exit(code=1) from exc
    if as_json:
        _echo_json([e.to_dict() for e in found])
        return
    for e in found:
        where = e.group or "whole model"
        typer.echo(f"{e.field} {e.label}, {where} (step {e.nume_ordre}, {e.count} values):")
        for ext in (e.min, e.max):
            if ext is None:
                typer.echo(f"  {e.note}")
                continue
            xyz = ", ".join(f"{x:g}" for x in ext.xyz)
            typer.echo(f"  {ext.kind} {_g(ext.value)} at {ext.entity} {ext.entity_id} ({xyz})")


@results_app.command("reactions")
def results_reactions(
    path: RunPath,
    group: Annotated[
        list[str] | None, typer.Option("--group", "-g", help="Group (repeatable).")
    ] = None,
    as_json: JsonFlag = False,
) -> None:
    """Reaction sums: whole model and per group from REAC_NODA, and from printed tables."""
    res, tables = _open_results(path)
    with res:
        summary = res.reactions(groups=group or [], tables=tables)
    if as_json:
        _echo_json(summary.to_dict())
        return

    def line(name: str, comps: dict[str, float]) -> str:
        return f"{name}: " + ", ".join(f"{c} {_g(v)}" for c, v in comps.items())

    if summary.total:
        typer.echo(line(f"all supports ({summary.field})", summary.total))
    for g in summary.per_group + summary.from_tables:
        typer.echo(line(g.group or g.source, g.components))
    for note in summary.notes:
        typer.echo(f"note: {note}")


@results_app.command("modal")
def results_modal(path: RunPath, as_json: JsonFlag = False) -> None:
    """Modal table: frequency, period, effective mass fractions and their cumulative sums."""
    res, tables = _open_results(path)
    with res:
        table = res.modal(tables)
    if as_json:
        _echo_json(table.to_dict())
        return
    typer.echo(f"modal result {table.result}; total mass {_g(table.total_mass)}")

    def pct(values: dict[str, float]) -> str:
        return " ".join(
            f"{100 * values[a]:5.1f}" if a in values else "    -" for a in ("DX", "DY", "DZ")
        )

    typer.echo("mode  frequency [Hz]  period [s]  effective mass % X Y Z  cumulative % X Y Z")
    for m in table.modes:
        typer.echo(
            f"{m.nume_ordre:4d}  {m.frequency_hz:14.4f}  {_g(m.period_s):>10}  "
            f"{pct(m.effective_mass_fraction):>22}  {pct(m.cumulative_fraction)}"
        )
    for note in table.notes:
        typer.echo(f"note: {note}")


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
