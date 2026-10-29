"""English engineering report from a code_aster job directory (task 4.6, ``docs/REPORT-SPEC.md``).

``collect(job)`` builds the :class:`RunModel` (JSON-ready, every number with its source);
``build(job, config, out)`` writes ``report.md``, ``report.html``, ``report.pdf`` and
``run_model.json``. Markdown is the source of truth; HTML is rendered from it with Jinja2 and
the PDF from the HTML with WeasyPrint (optional extra ``report``).
"""

from codeaster_en.report import collect as collect_module
from codeaster_en.report.collect import ALL_SECTIONS, Config, RunModel, collect, find_files
from codeaster_en.report.render import BuildResult, build, render_html, render_markdown, write_pdf
from codeaster_en.report.tripwire import french_words

__all__ = [
    "ALL_SECTIONS",
    "BuildResult",
    "Config",
    "RunModel",
    "build",
    "collect_module",
    "collect",
    "find_files",
    "french_words",
    "render_html",
    "render_markdown",
    "write_pdf",
]
