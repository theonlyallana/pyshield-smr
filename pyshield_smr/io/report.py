"""Report rendering (Markdown + HTML).

Uses Jinja2 for templating. The templates live under
``reports/templates/report.md.j2`` and ``reports/templates/report.html.j2``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape


TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "reports" / "templates"

# Accepted format aliases → canonical template suffix.
# Users may write "markdown" or "md" in their YAML spec; both map to report.md.j2.
_FORMAT_ALIASES: Dict[str, str] = {
    "markdown": "md",
    "md": "md",
    "html": "html",
    "htm": "html",
}


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_ROOT)),
        autoescape=select_autoescape(["html", "htm", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_report(
    context: Dict[str, Any],
    *,
    formats: tuple[str, ...] = ("md", "html"),
) -> Dict[str, str]:
    """Render the report templates with ``context`` and return ``{format: text}``.

    The ``formats`` tuple accepts both canonical names (``"md"``, ``"html"``) and
    aliases (``"markdown"``, ``"htm"``).  The output dict is keyed by the canonical
    suffix so callers always get ``"md"`` and ``"html"`` as keys.
    """
    env = _env()
    out: Dict[str, str] = {}
    for fmt in formats:
        canonical = _FORMAT_ALIASES.get(fmt.lower(), fmt.lower())
        tpl_name = f"report.{canonical}.j2"
        template = env.get_template(tpl_name)
        out[canonical] = template.render(**context)
    return out
