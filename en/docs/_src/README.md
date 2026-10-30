# French source documents

The official code_aster documents that `en/docs/` translates (PLAN task 5.2), as text extracted
from the French PDFs by `caen docs ingest` / `caen docs fetch` (task 5.1). Nothing here is
hand-edited; [INDEX.md](INDEX.md) lists the documents.

- `<DOC-ID>.fr.json`: page 1 header fields, the blocks in reading order (title, numbered
  headings, paragraphs, list items, syntax and listing blocks with their Courier columns
  kept, ruled and unruled tables, figure markers) and the translation chunks. Layout:
  `docs/schemas/doc-source.schema.json`.
- `<DOC-ID>.fr.md`: the same content as Markdown, for review and for citing a page (`<!-- page N -->`
  and `<!-- chunk N -->` markers).

The PDFs themselves are not committed; `caen docs fetch` downloads them into `.cache/docs-pdf/`
(git-ignored). `tests/fixtures/docs/U4.21.01.pdf` is the one copy kept, for the golden test.

## Source and version

Downloaded from `https://code-aster.org/doc/default/fr/man_<m>/<fascicle>/<doc>.pdf`, which the
site redirects to `/doc/v16/…` (October 2026). The page headers say "Code_Aster Version default"
and carry a document date and revision hash, both recorded per document. These are the current
documentation of the stable line, not documents tied to our pinned upstream tag: where a
document and the catalog extracted from upstream disagree, the catalog (`en/commands/*.json`)
wins (CLAUDE.md §2 rule 6).

What the extraction cannot give back: formulas typeset with OpenSymbol/Times come out as loose
characters (the block carries `"equation": true`, rendered as `<!-- equation -->`), and figures
are only marked (`*[Figure, page N: not extracted]*`).

## Licence

Copyright EDF R&D. Every page of every document ingested so far carries the notice
"Document diffusé sous licence GNU FDL (http://www.gnu.org/copyleft/fdl.html)". The notice
names no version, so under GFDL section 10 any published version may be used; we use
version 1.3 ([LICENSE-GFDL-1.3.txt](LICENSE-GFDL-1.3.txt)). These files are verbatim copies of
the text (GFDL section 2) with the copyright and licence notice kept in each file's header and
`licence` field. Translations made from them (`en/docs/`) are modified versions under the same
licence (GFDL section 4), not GPL; see `docs/LICENSING.md` and ADR-026.
