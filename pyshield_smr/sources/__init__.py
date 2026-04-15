"""Source-term generation and spectral handling."""

from .source_term import LineSource, SourceBundle, build_source_from_inventory
from .spectra import aggregate_lines

__all__ = ["LineSource", "SourceBundle", "aggregate_lines", "build_source_from_inventory"]
