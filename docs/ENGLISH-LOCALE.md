# Running code_aster with English messages

Task 3.4, ADR-004 and ADR-018. This page says how to make the solver print our English
messages itself, what stays French, and how the overlay keeps the catalog current.

## What we ship

| File | Committed | Made by | Use |
|---|---|---|---|
| `en/messages/<FAMILY>.en.json` | yes | extractor + translators | the only place English message text is edited |
| `en/messages/codeaster_en.po` | yes, generated | `caen translate gettext` | reviewable gettext catalog, domain `aster_messages` |
| `<localedir>/en/LC_MESSAGES/aster_messages.mo` | no | `caen translate gettext --mo <localedir>` | what the solver loads |

The `.po` has 6,813 entries: every message of `en/messages` with an English text, except the 15
bare strings upstream never passes to `_()` and the 7 log-structure lines kept French on purpose
(below), plus the four box footers ("This is a warning. …").
Each entry names its message IDs, source line and translation method (`machine` or `assisted`;
nothing is `reviewed` yet). Messages with placeholders carry `python-format`, so
`msgfmt --check` verifies the English uses the same directives.

## Build the catalog

```bash
pip install -e "tools[dev]"
caen translate gettext --mo build/locale
# wrote en/messages/codeaster_en.po (6813 entries)
# wrote build/locale/en/LC_MESSAGES/aster_messages.mo
# msgfmt: 6813 translated messages.
```

The `.mo` is written by our own code and needs no system tool; `msgfmt` (package `gettext`)
is only an extra check and is skipped when it is not installed. After editing any
`en/messages/*.en.json`, run `caen translate gettext` again and commit the `.po`: `caen validate`
fails while it is out of date.

## Switch a run to English

Two things are needed, and both are required.

1. **`DEBUT(LANG="EN")` in the command file.** `LANG` is an existing `DEBUT` keyword, so nothing
   is renamed. It makes `code_aster/Utilities/i18n.py` load domain `aster_messages` for the
   languages `EN`, `en` and any `en*` directory under the locale directory. The
   ClearFEA `.comm` builder (Phase 6) always emits it.
2. **The `.mo` where the solver looks.** The locale directory is `$ASTER_LOCALEDIR`, but the
   image's `share/aster/profile.sh` sets it on every run to
   `${RUNASTER_ROOT}/share/locale/aster`, so `docker run -e ASTER_LOCALEDIR=…` has no effect.
   Mount the directory that holds `en/LC_MESSAGES/aster_messages.mo` at that path instead.

With the pinned image (`CONTAINER_IMAGE`, ADR-011):

```bash
IMG="$(grep -v '^#' CONTAINER_IMAGE | tr -d '[:space:]')"
# install prefix = default RUNASTER_ROOT in the image's profile.sh
PREFIX="$(docker run --rm "$IMG" bash -c 'source /opt/activate.sh && sed -n "s/^: \${RUNASTER_ROOT:=\(.*\)}$/\1/p" "$(dirname "$(command -v run_aster)")/../share/aster/profile.sh"')"
docker run --rm -v "$PWD/build/locale:$PREFIX/share/locale/aster:ro" \
  -v "$PWD/study:/work" -w /work "$IMG" \
  bash -c 'source /opt/activate.sh && run_aster run.export'
```

For 17.4.22 the prefix is
`/opt/spack/opt/spack/linux-zen2/code-aster-17.4.22-qvronprjirskcxaala43j55z7obyclfv`; it
changes with every image, so look it up rather than hard-coding it. In an image you build
yourself, copy the `.mo` to `$PREFIX/share/locale/aster/en/LC_MESSAGES/` instead of mounting
it. Setting the system locale (`LANG=en_US.UTF-8`) changes nothing: only `DEBUT(LANG=…)` does.

`FIXTURE_LANG=EN scripts/run-fixture.sh tests/fixtures/<case>` does all of the above for a
fixture: it builds the `.mo`, adds `LANG="EN"` to a copy of `run.comm`, and writes
`tests/fixtures/<case>/output_en/`. The `english` job of
`.github/workflows/solver-fixtures.yml` runs it for `solid_static`, `shell_static`, `modal`
and `broken_missing_group`.

## What becomes English and what does not

From the committed English runs (`tests/fixtures/*/output_en/run.mess`):

- **English:** diagnostics boxes of the analysis commands (`<A> <MODELISA8_14>`,
  `<EXCEPTION> <MODELISA7_77>`, `CATAMESS_89` warning list), their footers, and the
  informational messages of families first used after `DEBUT` ("MED name of the mesh: mesh",
  "Checking the mesh.", "Element catalogs read again.").
- **Still French:**
  - on purpose (`KEEP_FRENCH` in `gettext_po.py`): `<I> <FIN> ARRET NORMAL …` (`SUPERVIS2_99`),
    which `run_aster` looks for to decide a run ended normally, and the stage lines
    `# Commande #`, `# Résultat commande #`, `# Mémoire (Mo)`, `# Fin commande #`,
    `# Dépend de` (`SUPERVIS2_71`–`75`, `80`), which log readers key on;
  - families imported before `DEBUT` applies `LANG`, because `_()` runs once at import:
    `SUPERVIS` and, when `CODE` or `--test` makes `DEBUT` print first, also `SUPERVIS2` (the
    `# Commande #…` stage lines and the CPU time lines). Which families this hits depends
    on what `DEBUT` prints before line 229 of `debut.py`;
  - the banner and lines that are not catalog messages or are printed through another path
    (`JEVEUX` statistics, the `<I> <FIN> ARRET NORMAL …` and `MEMOIRE JEVEUX …` lines,
    "Ouverture en écriture du fichier …"); the renderer translates the ones it knows;
  - the 15 bare strings and anything printed before `DEBUT`.

The runtime renderer (`caen mess translate`, tasks 4.3–4.4) handles both kinds of lines in one
log: French bodies are matched against the French templates, English bodies against the English
ones (`already_english: true` in its JSON), so arguments, IDs and the failed-command headline
come out the same as for a French run. A log produced with an older catalog than the current
`en/messages` can have English bodies that no longer match; regenerate it.

Fixing the French leaks needs upstream changes, listed in ADR-004 as proposed contributions:
apply `LANG` before the first `UTMESS` in `DEBUT`, wrap the 15 bare strings in `_()`.
