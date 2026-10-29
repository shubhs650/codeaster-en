# codeaster-en

English overlay for the [code_aster](https://code-aster.org) finite element solver, pinned to
one upstream release (the version's first three numbers: `17.4.26.1` is overlay build 1 for
code_aster 17.4.26).

It does not rename anything: code_aster commands and keywords stay French (`AFFE_MODELE`,
`GROUP_MA`). The package explains them and reads the solver's output in English:

- `codeaster_en.comm`: typed Python builder that writes a French `.comm` file, checked against
  the pinned command catalog.
- `codeaster_en.mess`: parses a `.mess` log and renders its diagnostics in English.
- `codeaster_en.results`: reads MED results and tables, labelled with the glossary.
- `codeaster_en.report`: English engineering report (Markdown, HTML, PDF).
- `codeaster_en.data`: paths to the shipped data: command catalog and references, English
  messages, glossary, and the gettext catalog (`.po` and `.mo`) that `DEBUT(LANG='EN')` loads.

```bash
pip install codeaster-en            # extras: [report] PDF, [images] result pictures
caen mess translate job/run.mess    # English log
caen report job/                    # English report
```

Translations are machine or agent made and not yet reviewed by an engineer; each one records
its method. Not affiliated with or endorsed by EDF. "code_aster" is a trademark of EDF.

License: GPL-3.0-or-later. Source and documentation:
<https://github.com/shubhs650/codeaster-en>.
