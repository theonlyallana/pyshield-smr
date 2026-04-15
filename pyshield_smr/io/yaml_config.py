"""YAML configuration helpers.

PyYAML ≥ 6.0 follows YAML 1.2, which requires explicit +/- signs in float
exponents (``1.0e+6``, not ``1.0e6``). Many handwritten specs use the YAML 1.1
form (no sign). ``_Yaml11Loader`` adds a resolver that accepts both forms so
that analysts are not surprised by their numeric values silently becoming
strings.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import yaml


# ---------------------------------------------------------------------------
# YAML 1.1-compatible float resolver
# ---------------------------------------------------------------------------

_YAML11_FLOAT_RE = re.compile(
    r"^[-+]?"
    r"(?:(?:\d[\d_]*)\.?\d*|\.\d[\d_]*)"     # integer or decimal
    r"(?:[Ee][-+]?\d[\d_]*)?$"               # optional exponent (sign optional)
)

# Characters that can start a float literal (used by PyYAML's resolver machinery)
_YAML11_FLOAT_FIRST = list("-+0123456789.")


class _Yaml11Loader(yaml.SafeLoader):
    """SafeLoader extended to recognise YAML 1.1 float notation.

    The only difference from SafeLoader is that the implicit float resolver
    accepts exponents without an explicit sign (e.g. ``1.0e6`` → 1000000.0).
    """


_Yaml11Loader.add_implicit_resolver(
    "tag:yaml.org,2002:float",
    _YAML11_FLOAT_RE,
    _YAML11_FLOAT_FIRST,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_yaml_spec(path: str | Path) -> Dict[str, Any]:
    """Load a YAML spec file into a dict.

    Uses the YAML 1.1-compatible loader so that scientific notation without
    explicit signs (``1.0e6``, ``5e13``) is parsed as ``float``, matching the
    behaviour analysts expect when writing specs by hand.
    """
    text = Path(path).read_text(encoding="utf-8")
    return yaml.load(text, Loader=_Yaml11Loader)  # noqa: S506  (controlled loader)


def dump_yaml_spec(spec: Dict[str, Any], path: str | Path) -> None:
    """Dump a spec dict to a YAML file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(spec, f, sort_keys=False, allow_unicode=True)
